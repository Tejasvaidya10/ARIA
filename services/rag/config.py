from pydantic_settings import SettingsConfigDict

from services.shared.config import BaseServiceSettings


class RAGSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix="RAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "rag"
    embedding_model: str = "all-MiniLM-L6-v2"
    index_path: str = "data/faiss/case_index.faiss"
    case_store_path: str = "data/faiss/case_store.json"
    top_k: int = 5
    similarity_threshold: float = 0.3
    rate_limit: str = "30/minute"
