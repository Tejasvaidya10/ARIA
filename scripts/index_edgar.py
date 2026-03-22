"""Chunk SEC EDGAR Risk Factors text and add to the FAISS index.

Reads the plain text files downloaded by download_edgar.py, splits them
into meaningful paragraphs, runs each through the NER pipeline to extract
entities, embeds them, and appends to the existing FAISS index.

This enriches the RAG service with real corporate risk disclosures, so
similar-case retrieval includes both historical claims (from Kaggle) and
regulatory risk context (from 10-K filings).

Usage:
    python -m scripts.index_edgar
"""

import re
from pathlib import Path

import numpy as np

from services.ingestion.core.constants import INSURANCE_PATTERNS
from services.ingestion.services.ner_extractor import (
    extract_entities,
    load_nlp_pipeline,
    summarize_entities,
)
from services.rag.core.schemas import CaseRecord
from services.rag.services.embedder import embed_batch, entities_to_text, load_embedding_model
from services.rag.services.index_manager import FAISSIndexManager

EDGAR_DIR = Path("data/edgar")
INDEX_PATH = "data/faiss/case_index.faiss"
STORE_PATH = "data/faiss/case_store.json"
MIN_CHUNK_LEN = 200
MAX_CHUNK_LEN = 2000


def chunk_text(text: str) -> list[str]:
    """Split risk factors text into meaningful chunks.

    Tries to split on paragraph boundaries first, then sentence boundaries
    for oversized paragraphs. Drops chunks that are too short to be useful.
    """
    # Split on double newlines (paragraph breaks)
    raw_paragraphs = re.split(r"\n\s*\n", text)

    chunks = []
    for para in raw_paragraphs:
        para = para.strip()
        if len(para) < MIN_CHUNK_LEN:
            continue

        if len(para) <= MAX_CHUNK_LEN:
            chunks.append(para)
        else:
            # Split long paragraphs on sentence boundaries
            sentences = re.split(r"(?<=[.!?])\s+", para)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) > MAX_CHUNK_LEN and len(current) >= MIN_CHUNK_LEN:
                    chunks.append(current.strip())
                    current = sent
                else:
                    current = f"{current} {sent}" if current else sent
            if len(current) >= MIN_CHUNK_LEN:
                chunks.append(current.strip())

    return chunks


def extract_company_name(filename: str) -> str:
    """Extract company name from filename like 'aig_2026-02-12.txt'."""
    name = filename.rsplit("_", 1)[0]
    return name.replace("_", " ").title()


def main() -> None:
    edgar_files = sorted(EDGAR_DIR.glob("*.txt"))
    if not edgar_files:
        print(f"No EDGAR files found in {EDGAR_DIR}/")
        print("Run first: python -m scripts.download_edgar")
        raise SystemExit(1)

    print(f"found {len(edgar_files)} EDGAR filings")

    # Load NER pipeline for entity extraction
    print("loading spaCy NER pipeline...")
    nlp = load_nlp_pipeline("en_core_web_sm", INSURANCE_PATTERNS)

    # Chunk all filings
    all_chunks: list[str] = []
    chunk_sources: list[str] = []

    for filepath in edgar_files:
        company = extract_company_name(filepath.name)
        text = filepath.read_text()
        chunks = chunk_text(text)
        all_chunks.extend(chunks)
        chunk_sources.extend([company] * len(chunks))
        print(f"  {company}: {len(chunks)} chunks from {len(text):,} chars")

    print(f"total chunks: {len(all_chunks)}")

    # Run NER on each chunk to extract entities
    print("extracting entities from chunks...")
    all_entity_summaries: list[dict[str, list[str]]] = []
    all_records: list[CaseRecord] = []

    for i, (chunk, source) in enumerate(zip(all_chunks, chunk_sources, strict=True)):
        entities = extract_entities(chunk, nlp)
        summary = summarize_entities(entities)
        all_entity_summaries.append(summary)

        # Create a case record for each chunk
        entity_labels = [f"{k}: {', '.join(v[:3])}" for k, v in summary.items() if v]
        brief = "; ".join(entity_labels)[:200] if entity_labels else chunk[:200]

        record = CaseRecord(
            case_id=10000 + i,  # offset to avoid collisions with Kaggle cases
            policy_id=f"EDGAR-{source.upper().replace(' ', '-')}-{i:04d}",
            summary=brief,
            outcome=f"10-K risk disclosure from {source}",
            risk_tier="INFO",
            claim_amount=0.0,
        )
        all_records.append(record)

    # Embed chunks using entity text (same format as Kaggle cases)
    print("loading embedding model...")
    model = load_embedding_model("all-MiniLM-L6-v2")

    texts = [entities_to_text(s) for s in all_entity_summaries]
    # For chunks where NER found nothing, use the raw text instead
    for i, (t, chunk) in enumerate(zip(texts, all_chunks, strict=True)):
        if t == "empty submission":
            texts[i] = chunk[:500]

    print(f"embedding {len(texts)} chunks...")
    vectors = embed_batch(model, texts)

    # Load existing index and append
    print("loading existing FAISS index...")
    manager = FAISSIndexManager(dimension=vectors.shape[1])
    manager.load(INDEX_PATH, STORE_PATH)
    existing_count = manager.total_indexed

    manager.add(vectors, all_records)
    manager.save(INDEX_PATH, STORE_PATH)

    new_count = manager.total_indexed
    print(
        f"index updated: {existing_count} -> {new_count} vectors (+{new_count - existing_count})"
    )
    print(f"  index: {INDEX_PATH}")
    print(f"  store: {STORE_PATH}")

    # Sanity check: search for terrorism risk
    query = embed_batch(model, ["terrorism catastrophe reinsurance exposure"])
    results = manager.search(query, top_k=3)
    print("\nsanity check — top 3 matches for 'terrorism catastrophe reinsurance':")
    for r in results:
        print(f"  {r.policy_id}: {r.similarity_score:.4f}")
        print(f"    {r.summary[:120]}")


if __name__ == "__main__":
    np.random.seed(42)
    main()
