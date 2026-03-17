from pydantic_settings import SettingsConfigDict

from services.shared.config import BaseServiceSettings


class IngestionSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix="INGESTION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "ingestion"
    spacy_model_path: str = "en_core_web_sm"
    spark_master: str = "local[*]"
    spark_app_name: str = "aria-ingestion"
    max_upload_size_mb: int = 25
    max_pages: int = 200
    rate_limit: str = "10/minute"
    spacy_batch_size: int = 1000
