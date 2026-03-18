from pydantic import BaseModel, Field

from services.shared.schemas import RiskFactor, RiskTier


class PredictionRequest(BaseModel):
    submission_id: str
    entity_summary: dict[str, list[str]]
    full_text: str = ""


class PredictionResponse(BaseModel):
    submission_id: str
    risk_tier: RiskTier
    risk_probability: float = Field(ge=0.0, le=1.0)
    predicted_claim_amount: float
    key_risk_factors: list[RiskFactor]
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float
