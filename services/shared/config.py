from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base config that every ARIA service inherits from.

    Reads values from environment variables and .env files automatically.
    Subclasses just declare their fields and pydantic-settings handles the rest.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str
    log_level: str = "INFO"
    debug: bool = False
