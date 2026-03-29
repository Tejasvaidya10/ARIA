from enum import StrEnum

from pydantic import BaseModel, Field


class RiskTier(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskFactor(BaseModel):
    name: str
    shap_value: float
    direction: str = Field(description="'increases_risk' or 'decreases_risk'")


class SimilarCase(BaseModel):
    policy_id: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    summary: str
    outcome: str | None = None


class HallucinationCheck(BaseModel):
    detected: bool
    count: int
    flags: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class SubmissionAnalysis(BaseModel):
    submission_id: str
    risk_tier: RiskTier
    risk_probability: float = Field(ge=0.0, le=1.0)
    predicted_claim_amount: float
    key_risk_factors: list[RiskFactor]
    underwriter_narrative: str
    similar_cases: list[SimilarCase]
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float
    hallucination_check: HallucinationCheck | None = None
