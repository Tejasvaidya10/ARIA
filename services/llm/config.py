from pydantic_settings import SettingsConfigDict

from services.shared.config import BaseServiceSettings


class LLMSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "llm"
    provider: str = "ollama"

    # Anthropic (Claude)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6-20250514"

    # Ollama (local dev)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Downstream service URLs
    prediction_service_url: str = "http://localhost:8001"
    rag_service_url: str = "http://localhost:8002"

    # Orchestration
    max_tool_rounds: int = 5
    rate_limit: str = "10/minute"
    request_timeout: float = 30.0
    enable_hallucination_check: bool = False
    audit_log_path: str = "data/audit/audit_trail.jsonl"
