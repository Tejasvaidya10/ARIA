import pytest

from services.ingestion.core.constants import INSURANCE_PATTERNS
from services.ingestion.core.schemas import InsuranceEntity
from services.ingestion.services.ner_extractor import (
    deduplicate_entities,
    extract_entities,
    load_nlp_pipeline,
    summarize_entities,
)


@pytest.fixture(scope="module")
def nlp():  # type: ignore[no-untyped-def]
    return load_nlp_pipeline("en_core_web_sm", INSURANCE_PATTERNS)


def test_extracts_coverage_type(nlp) -> None:  # type: ignore[no-untyped-def]
    entities = extract_entities("The policy covers commercial general liability.", nlp)
    labels = [e.label for e in entities]
    assert "COVERAGE_TYPE" in labels


def test_extracts_peril(nlp) -> None:  # type: ignore[no-untyped-def]
    entities = extract_entities("Previous claims include fire and water damage.", nlp)
    labels = [e.label for e in entities]
    assert "PERIL" in labels


def test_extracts_money(nlp) -> None:  # type: ignore[no-untyped-def]
    entities = extract_entities("Premium amount is $50,000.", nlp)
    labels = [e.label for e in entities]
    assert "MONEY" in labels


def test_extracts_policy_number(nlp) -> None:  # type: ignore[no-untyped-def]
    entities = extract_entities("Policy PLY-2024-00892 is active.", nlp)
    texts = [e.text for e in entities]
    assert "PLY-2024-00892" in texts


def test_deduplicate_keeps_highest_confidence() -> None:
    entities = [
        InsuranceEntity(text="fire", label="PERIL", start_char=0, end_char=4, confidence=0.85),
        InsuranceEntity(text="fire", label="PERIL", start_char=20, end_char=24, confidence=1.0),
    ]
    deduped = deduplicate_entities(entities)
    assert len(deduped) == 1
    assert deduped[0].confidence == 1.0


def test_summarize_groups_by_label() -> None:
    entities = [
        InsuranceEntity(text="fire", label="PERIL", start_char=0, end_char=4),
        InsuranceEntity(text="flood", label="PERIL", start_char=10, end_char=15),
        InsuranceEntity(text="$50,000", label="MONEY", start_char=20, end_char=27),
    ]
    summary = summarize_entities(entities)
    assert summary["PERIL"] == ["fire", "flood"]
    assert summary["MONEY"] == ["$50,000"]
