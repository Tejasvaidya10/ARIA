"""Generate synthetic historical insurance cases and build a FAISS index.

This creates a searchable vector database of past cases so the RAG service
can find similar cases when evaluating a new submission. In production,
these cases would come from a real claims management system.

Usage:
    python -m scripts.build_case_index
"""

import random

import numpy as np

from services.rag.core.schemas import CaseRecord
from services.rag.services.embedder import embed_batch, entities_to_text, load_embedding_model
from services.rag.services.index_manager import FAISSIndexManager

PERILS = [
    "fire",
    "flood",
    "earthquake",
    "wind",
    "hail",
    "lightning",
    "theft",
    "vandalism",
    "water damage",
    "cyber attack",
]
COVERAGES = [
    "general liability",
    "property",
    "business interruption",
    "professional liability",
    "cyber liability",
    "umbrella",
    "workers compensation",
    "commercial auto",
    "directors and officers",
]
PROPERTY_TYPES = [
    "office",
    "warehouse",
    "retail",
    "restaurant",
    "manufacturing",
    "residential",
    "hotel",
    "hospital",
    "school",
    "data center",
]
CLAIM_STATUSES = ["open", "closed", "denied", "pending review", "settled"]
OUTCOMES = [
    "claim approved, paid ${amount}",
    "claim denied due to exclusion",
    "claim settled for ${amount}",
    "no claim filed during policy term",
    "partial claim approved for ${amount}",
    "claim pending litigation",
]
RISK_TIERS = ["LOW", "MODERATE", "HIGH", "CRITICAL"]


def _random_money() -> str:
    amount = random.choice(
        [
            random.randint(10_000, 500_000),
            random.randint(500_000, 5_000_000),
            random.randint(1_000_000, 50_000_000),
        ]
    )
    return f"${amount:,}"


def _generate_case(case_id: int) -> tuple[dict[str, list[str]], CaseRecord]:
    """Generate one synthetic case with entities and metadata."""
    num_perils = random.randint(1, 4)
    num_coverages = random.randint(1, 5)
    num_money = random.randint(0, 3)

    entities: dict[str, list[str]] = {
        "PERIL": random.sample(PERILS, num_perils),
        "COVERAGE_TYPE": random.sample(COVERAGES, num_coverages),
        "PROPERTY_TYPE": [random.choice(PROPERTY_TYPES)],
        "MONEY": [_random_money() for _ in range(num_money)],
    }

    if random.random() > 0.4:
        entities["CLAIM_STATUS"] = [random.choice(CLAIM_STATUSES)]

    policy_id = f"PLY-{random.randint(2018, 2025)}-{case_id:05d}"

    perils_str = ", ".join(entities["PERIL"])
    prop = entities["PROPERTY_TYPE"][0]
    summary = f"{prop} property with {perils_str} exposure"

    claim_amount = random.uniform(0, 10_000_000)
    outcome_template = random.choice(OUTCOMES)
    outcome = outcome_template.replace("${amount}", f"${claim_amount:,.0f}")

    tier_weights = [0.3, 0.35, 0.25, 0.1]
    risk_tier = random.choices(RISK_TIERS, weights=tier_weights, k=1)[0]

    record = CaseRecord(
        case_id=case_id,
        policy_id=policy_id,
        summary=summary,
        outcome=outcome,
        risk_tier=risk_tier,
        claim_amount=round(claim_amount, 2),
    )

    return entities, record


def main() -> None:
    num_cases = 500
    print(f"generating {num_cases} synthetic cases...")

    all_entities: list[dict[str, list[str]]] = []
    all_records: list[CaseRecord] = []

    for i in range(num_cases):
        entities, record = _generate_case(i)
        all_entities.append(entities)
        all_records.append(record)

    print("loading embedding model (first run downloads ~80MB)...")
    model = load_embedding_model("all-MiniLM-L6-v2")

    texts = [entities_to_text(e) for e in all_entities]
    print(f"embedding {len(texts)} cases...")
    vectors = embed_batch(model, texts)

    manager = FAISSIndexManager(dimension=vectors.shape[1])
    manager.add(vectors, all_records)

    index_path = "data/faiss/case_index.faiss"
    store_path = "data/faiss/case_store.json"
    manager.save(index_path, store_path)

    print(f"index saved: {manager.total_indexed} vectors ({vectors.shape[1]}d)")
    print(f"  index: {index_path}")
    print(f"  store: {store_path}")

    # quick sanity check — search for a case similar to the first one
    query = embed_batch(model, [texts[0]])
    results = manager.search(query, top_k=3)
    print("\nsanity check — top 3 matches for case 0:")
    for r in results:
        print(f"  {r.policy_id}: {r.similarity_score:.4f} — {r.summary}")


if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)
    main()
