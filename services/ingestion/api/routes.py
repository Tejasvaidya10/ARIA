import structlog
from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import JSONResponse
from pyspark.sql import SparkSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from spacy.language import Language

from services.ingestion.api.dependencies import get_nlp, get_settings, get_spark
from services.ingestion.config import IngestionSettings
from services.ingestion.core.schemas import ExtractedDocument
from services.ingestion.services import pdf_sanitizer, spark_pipeline
from services.shared.exceptions import ExtractionError

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["extraction"])


@router.post("/extract", response_model=ExtractedDocument)
@limiter.limit("10/minute")
async def extract_document(
    request: Request,
    file: UploadFile,
    settings: IngestionSettings = Depends(get_settings),
    spark: SparkSession = Depends(get_spark),
    nlp: Language = Depends(get_nlp),
) -> ExtractedDocument | JSONResponse:
    try:
        pdf_bytes = await pdf_sanitizer.validate_upload(file, settings)
    except ExtractionError as exc:
        await logger.awarning("pdf_validation_failed", error=str(exc), filename=file.filename)
        return JSONResponse(status_code=400, content={"error": str(exc)})

    try:
        result = spark_pipeline.run_extraction_pipeline(
            spark, nlp, pdf_bytes, file.filename or "unknown.pdf"
        )
    except Exception as exc:
        await logger.aerror("extraction_failed", error=str(exc), filename=file.filename)
        return JSONResponse(status_code=500, content={"error": "Extraction failed"})

    await logger.ainfo(
        "extraction_complete",
        submission_id=result.submission_id,
        filename=result.filename,
        page_count=result.page_count,
        entity_count=len(result.entities),
        processing_time_ms=result.processing_time_ms,
    )
    return result
