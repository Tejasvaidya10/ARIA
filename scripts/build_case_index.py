"""Build a FAISS index from real Kaggle Auto Insurance Claims data.

Reads data/raw/insurance_claims.csv, converts each claim into an entity summary
(same format the NER pipeline produces), embeds the text, and stores everything
in a FAISS index for the RAG service to search.

Usage:
    python -m scripts.build_case_index
"""

import csv
from pathlib import Path

import numpy as np

from services.rag.core.schemas import CaseRecord
from services.rag.services.embedder import embed_batch, entities_to_text, load_embedding_model
from services.rag.services.index_manager import FAISSIndexManager

DATA_PATH = Path("data/raw/insurance_claims.csv")
INDEX_PATH = "data/faiss/case_index.faiss"
STORE_PATH = "data/faiss/case_store.json"

RISK_TIERS = {
    "Trivial Damage": "LOW",
    "Minor Damage": "MODERATE",
    "Major Damage": "HIGH",
    "Total Loss": "CRITICAL",
}


def row_to_case(case_id: int, row: dict[str, str]) -> tuple[dict[str, list[str]], CaseRecord]:
    """Convert a CSV row into an entity summary and a CaseRecord."""
    entities: dict[str, list[str]] = {}

    # Incident type as peril
    incident = row.get("incident_type", "")
    if incident:
        entities["PERIL"] = [incident.lower()]
    if row.get("property_damage", "").upper() == "YES":
        entities.setdefault("PERIL", []).append("property damage")

    # Coverage info
    coverages = []
    csl = row.get("policy_csl", "")
    if csl:
        coverages.append(f"CSL {csl}")
    umbrella = int(row.get("umbrella_limit", "0") or "0")
    if umbrella > 0:
        coverages.append(f"umbrella ${umbrella:,}")
    if coverages:
        entities["COVERAGE_TYPE"] = coverages

    # Money (pre-claim info only)
    premium = row.get("policy_annual_premium", "")
    if premium and premium != "?":
        entities["MONEY"] = [f"${float(premium):,.2f}"]

    # Severity as claim status
    severity = row.get("incident_severity", "")
    if severity:
        entities["CLAIM_STATUS"] = [severity.lower()]

    # Vehicle
    make = row.get("auto_make", "")
    model_name = row.get("auto_model", "")
    if make:
        entities["VEHICLE"] = [f"{make} {model_name}".strip()]

    # Build case record
    total_claim = float(row.get("total_claim_amount", "0") or "0")
    risk_tier = RISK_TIERS.get(severity, "MODERATE")
    fraud = row.get("fraud_reported", "N")

    summary_parts = []
    if incident:
        summary_parts.append(incident.lower())
    if make:
        summary_parts.append(f"{make} {model_name}")
    summary_parts.append(f"in {row.get('incident_state', '?')}")
    summary_parts.append(f"severity: {severity.lower()}")

    outcome = f"claim ${total_claim:,.0f}"
    if fraud == "Y":
        outcome += " (fraud reported)"
    else:
        outcome += " (no fraud)"

    record = CaseRecord(
        case_id=case_id,
        policy_id=row.get("policy_number", str(case_id)),
        summary=", ".join(summary_parts),
        outcome=outcome,
        risk_tier=risk_tier,
        claim_amount=total_claim,
    )

    return entities, record


def main() -> None:
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found.")
        print(
            "Download: kaggle datasets download -d buntyshah/auto-insurance-claims-data -p data/raw/ --unzip"
        )
        raise SystemExit(1)

    print("loading claims data...")
    all_entities: list[dict[str, list[str]]] = []
    all_records: list[CaseRecord] = []

    with open(DATA_PATH) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            entities, record = row_to_case(i, row)
            all_entities.append(entities)
            all_records.append(record)

    print(f"  loaded {len(all_records)} claims")

    print("loading embedding model...")
    model = load_embedding_model("all-MiniLM-L6-v2")

    texts = [entities_to_text(e) for e in all_entities]
    print(f"embedding {len(texts)} cases...")
    vectors = embed_batch(model, texts)

    Path(INDEX_PATH).parent.mkdir(parents=True, exist_ok=True)
    manager = FAISSIndexManager(dimension=vectors.shape[1])
    manager.add(vectors, all_records)
    manager.save(INDEX_PATH, STORE_PATH)

    print(f"index saved: {manager.total_indexed} vectors ({vectors.shape[1]}d)")
    print(f"  index: {INDEX_PATH}")
    print(f"  store: {STORE_PATH}")

    # sanity check — search for a case similar to the first one
    query = embed_batch(model, [texts[0]])
    results = manager.search(query, top_k=3)
    print("\nsanity check — top 3 matches for case 0:")
    for r in results:
        print(f"  {r.policy_id}: {r.similarity_score:.4f} — {r.summary}")


if __name__ == "__main__":
    np.random.seed(42)
    main()
