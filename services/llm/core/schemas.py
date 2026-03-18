from pydantic import BaseModel, Field

from services.shared.schemas import RiskFactor, RiskTier, SimilarCase


class SynthesisRequest(BaseModel):
    submission_id: str
    entity_summary: dict[str, list[str]]
    full_text: str = ""


class SynthesisResult(BaseModel):
    """Internal result from the LLM provider.

    The route handler wraps this into SubmissionAnalysis by adding
    submission_id and processing_time_ms.
    """

    risk_tier: RiskTier
    risk_probability: float = Field(ge=0.0, le=1.0)
    predicted_claim_amount: float
    key_risk_factors: list[RiskFactor]
    underwriter_narrative: str
    similar_cases: list[SimilarCase]
    confidence_score: float = Field(ge=0.0, le=1.0)
