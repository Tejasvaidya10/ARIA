from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic.types import TextBlock

from services.llm.core.schemas import SynthesisResult
from services.llm.services.hallucination import detect_hallucinations
from services.shared.schemas import RiskFactor, RiskTier, SimilarCase


@pytest.fixture()
def synthesis_result() -> SynthesisResult:
    return SynthesisResult(
        risk_tier=RiskTier.HIGH,
        risk_probability=0.75,
        predicted_claim_amount=120000.0,
        key_risk_factors=[
            RiskFactor(name="Police Involvement", shap_value=0.3, direction="increases_risk")
        ],
        underwriter_narrative="This is a high risk submission due to police involvement.",
        similar_cases=[
            SimilarCase(
                policy_id="POL-001",
                similarity_score=0.88,
                summary="Vehicle collision with police report",
                outcome="approved",
            )
        ],
        confidence_score=0.7,
    )


async def test_detect_hallucinations_clean(synthesis_result: SynthesisResult) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        TextBlock(
            type="text",
            text='{"hallucination_detected": false, "hallucination_count": 0, "details": [], "confidence": 0.9}',
        )
    ]

    with patch("services.llm.services.hallucination.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        result = await detect_hallucinations(
            synthesis_result.underwriter_narrative,
            {"PERIL": ["fire"]},
            synthesis_result,
            api_key="test-key",
            model="claude-sonnet-4-6-20250514",
        )

    assert result.detected is False
    assert result.count == 0
    assert result.flags == []
    assert result.confidence == pytest.approx(0.9)


async def test_detect_hallucinations_found(synthesis_result: SynthesisResult) -> None:
    mock_response = MagicMock()
    mock_response.content = [
        TextBlock(
            type="text",
            text='{"hallucination_detected": true, "hallucination_count": 2, "details": ["fabricated $1M statistic", "ghost policy POL-999"], "confidence": 0.8}',
        )
    ]

    with patch("services.llm.services.hallucination.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        result = await detect_hallucinations(
            synthesis_result.underwriter_narrative,
            {"PERIL": ["fire"]},
            synthesis_result,
            api_key="test-key",
            model="claude-sonnet-4-6-20250514",
        )

    assert result.detected is True
    assert result.count == 2
    assert len(result.flags) == 2


async def test_detect_hallucinations_api_failure(synthesis_result: SynthesisResult) -> None:
    with patch("services.llm.services.hallucination.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create.side_effect = Exception("API error")
        mock_cls.return_value = mock_client

        result = await detect_hallucinations(
            synthesis_result.underwriter_narrative,
            {},
            synthesis_result,
            api_key="test-key",
            model="claude-sonnet-4-6-20250514",
        )

    assert result.detected is False
    assert result.count == 0


async def test_detect_hallucinations_invalid_json(synthesis_result: SynthesisResult) -> None:
    mock_response = MagicMock()
    mock_response.content = [TextBlock(type="text", text="not valid json")]

    with patch("services.llm.services.hallucination.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        result = await detect_hallucinations(
            synthesis_result.underwriter_narrative,
            {},
            synthesis_result,
            api_key="test-key",
            model="claude-sonnet-4-6-20250514",
        )

    assert result.detected is False
    assert result.count == 0
