import httpx
import pytest

from services.llm.config import LLMSettings
from services.llm.core.schemas import SynthesisResult
from services.shared.schemas import RiskFactor, RiskTier, SimilarCase


class FakeLLMProvider:
    """Test double that returns a canned SynthesisResult.

    Satisfies the LLMProvider protocol without calling any real
    LLM or downstream service.
    """

    async def synthesize(
        self,
        entity_summary: dict[str, list[str]],
        full_text: str,
        http_client: httpx.AsyncClient,
        settings: LLMSettings,
    ) -> SynthesisResult:
        return SynthesisResult(
            risk_tier=RiskTier.MODERATE,
            risk_probability=0.45,
            predicted_claim_amount=35000.0,
            key_risk_factors=[
                RiskFactor(
                    name="has_fire_peril",
                    shap_value=0.12,
                    direction="increases_risk",
                ),
            ],
            underwriter_narrative=(
                "This submission presents moderate risk. Fire peril is the "
                "primary driver. Recommend approval with standard conditions."
            ),
            similar_cases=[
                SimilarCase(
                    policy_id="POL-001",
                    similarity_score=0.85,
                    summary="Commercial property with fire exposure",
                    outcome="approved with conditions",
                ),
            ],
            confidence_score=0.72,
        )


@pytest.fixture()
def fake_provider() -> FakeLLMProvider:
    return FakeLLMProvider()


@pytest.fixture()
def sample_entity_summary() -> dict[str, list[str]]:
    return {
        "PERIL": ["fire", "flood"],
        "MONEY": ["$50,000", "$500,000"],
        "COVERAGE_TYPE": ["commercial general liability"],
        "PROPERTY_TYPE": ["wood-frame residential"],
    }
