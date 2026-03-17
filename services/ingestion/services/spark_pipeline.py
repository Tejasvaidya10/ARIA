import time
import uuid

from pyspark.sql import SparkSession
from spacy.language import Language

from services.ingestion.config import IngestionSettings
from services.ingestion.core.schemas import (
    ExtractedDocument,
    InsuranceEntity,
    PageExtraction,
)
from services.ingestion.services import ner_extractor, text_extractor


def create_spark_session(settings: IngestionSettings) -> SparkSession:
    return (
        SparkSession.builder.master(settings.spark_master)
        .appName(settings.spark_app_name)
        .config("spark.ui.enabled", "false")
        .config("spark.driver.memory", "1g")
        .getOrCreate()
    )


def run_extraction_pipeline(
    spark: SparkSession,
    nlp: Language,
    pdf_bytes: bytes,
    filename: str,
) -> ExtractedDocument:
    start = time.perf_counter()
    submission_id = str(uuid.uuid4())

    # Extract text from all pages (driver-side, PyMuPDF can't be serialized)
    raw_pages = text_extractor.extract_all_pages(pdf_bytes)

    if not raw_pages:
        return ExtractedDocument(
            submission_id=submission_id,
            filename=filename,
            page_count=0,
            full_text="",
            pages=[],
            entities=[],
            entity_summary={},
            processing_time_ms=round((time.perf_counter() - start) * 1000, 2),
        )

    # Load page text into Spark DataFrame for distributed processing.
    # In local mode this runs in-process; scales to cluster mode unchanged.
    page_df = spark.createDataFrame(list(raw_pages), schema=["page_number", "text"])
    collected = page_df.collect()

    # NER runs on the driver because spaCy models aren't serializable across
    # Spark worker processes. For batch mode with many documents, switch to
    # mapPartitions with per-worker model loading.
    all_entities: list[InsuranceEntity] = []
    pages: list[PageExtraction] = []

    for row in collected:
        page_entities = ner_extractor.extract_entities(row["text"], nlp)
        pages.append(
            PageExtraction(
                page_number=row["page_number"],
                text=row["text"],
                entities=page_entities,
            )
        )
        all_entities.extend(page_entities)

    pages.sort(key=lambda p: p.page_number)
    deduped = ner_extractor.deduplicate_entities(all_entities)
    full_text = "\n\n".join(p.text for p in pages)

    return ExtractedDocument(
        submission_id=submission_id,
        filename=filename,
        page_count=len(pages),
        full_text=full_text,
        pages=pages,
        entities=deduped,
        entity_summary=ner_extractor.summarize_entities(deduped),
        processing_time_ms=round((time.perf_counter() - start) * 1000, 2),
    )
