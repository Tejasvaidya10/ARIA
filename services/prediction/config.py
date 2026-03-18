from pydantic_settings import SettingsConfigDict

from services.shared.config import BaseServiceSettings


class PredictionSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix="PREDICTION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "prediction"
    xgboost_model_path: str = "models/xgboost/claim_probability.json"
    xgboost_severity_model_path: str = "models/xgboost/claim_severity.json"
    rate_limit: str = "20/minute"
    risk_threshold_low: float = 0.25
    risk_threshold_moderate: float = 0.50
    risk_threshold_high: float = 0.75
