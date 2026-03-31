import asyncio
import json
from pathlib import Path

import pytest

from services.shared.schemas import HallucinationCheck, RiskTier, SubmissionAnalysis


@pytest.fixture
def analysis() -> SubmissionAnalysis:
    return SubmissionAnalysis(
        submission_id="audit-001",
        risk_tier=RiskTier.HIGH,
        risk_probability=0.78,
        predicted_claim_amount=48500.0,
        key_risk_factors=[],
        underwriter_narrative="Test narrative.",
        similar_cases=[],
        confidence_score=0.56,
        processing_time_ms=321.5,
        hallucination_check=None,
    )


def test_record_writes_correct_fields(tmp_path: Path, analysis: SubmissionAnalysis) -> None:
    from services.llm.services.audit import record

    audit_path = str(tmp_path / "audit_trail.jsonl")
    asyncio.run(record(analysis, audit_path, "ollama"))

    lines = Path(audit_path).read_text().strip().split("\n")
    assert len(lines) == 1
    event = json.loads(lines[0])

    assert event["submission_id"] == "audit-001"
    assert event["risk_tier"] == "HIGH"
    assert event["risk_probability"] == 0.78
    assert event["predicted_claim_amount"] == 48500.0
    assert event["confidence_score"] == 0.56
    assert event["processing_time_ms"] == 321.5
    assert event["similar_cases_count"] == 0
    assert event["hallucination_detected"] is None
    assert event["hallucination_confidence"] is None
    assert event["provider"] == "ollama"
    assert "timestamp" in event
    assert "request_id" in event


def test_record_writes_hallucination_fields(tmp_path: Path, analysis: SubmissionAnalysis) -> None:
    from services.llm.services.audit import record

    analysis.hallucination_check = HallucinationCheck(
        detected=True, count=1, flags=["flag1"], confidence=0.88
    )
    audit_path = str(tmp_path / "audit_trail.jsonl")
    asyncio.run(record(analysis, audit_path, "anthropic"))

    event = json.loads(Path(audit_path).read_text().strip())
    assert event["hallucination_detected"] is True
    assert event["hallucination_confidence"] == 0.88
    assert event["provider"] == "anthropic"


def test_record_appends_lines(tmp_path: Path, analysis: SubmissionAnalysis) -> None:
    from services.llm.services.audit import record

    audit_path = str(tmp_path / "audit_trail.jsonl")
    asyncio.run(record(analysis, audit_path, "ollama"))
    asyncio.run(record(analysis, audit_path, "ollama"))

    lines = Path(audit_path).read_text().strip().split("\n")
    assert len(lines) == 2


def test_record_creates_parent_directory(tmp_path: Path, analysis: SubmissionAnalysis) -> None:
    from services.llm.services.audit import record

    audit_path = str(tmp_path / "nested" / "dirs" / "audit_trail.jsonl")
    asyncio.run(record(analysis, audit_path, "ollama"))
    assert Path(audit_path).exists()


def test_record_does_not_raise_on_write_failure(
    tmp_path: Path, analysis: SubmissionAnalysis, monkeypatch: pytest.MonkeyPatch
) -> None:
    from services.llm.services import audit as audit_mod

    def failing_open(*args: object, **kwargs: object) -> object:
        raise OSError("disk full")

    monkeypatch.setattr(audit_mod, "open", failing_open)
    audit_path = str(tmp_path / "audit_trail.jsonl")
    # Must not raise
    asyncio.run(audit_mod.record(analysis, audit_path, "ollama"))
