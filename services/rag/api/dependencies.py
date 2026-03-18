from fastapi import Request
from sentence_transformers import SentenceTransformer

from services.rag.config import RAGSettings
from services.rag.services.index_manager import FAISSIndexManager


def get_settings(request: Request) -> RAGSettings:
    settings: RAGSettings = request.app.state.settings
    return settings


def get_embedding_model(request: Request) -> SentenceTransformer:
    model: SentenceTransformer = request.app.state.embedding_model
    return model


def get_index_manager(request: Request) -> FAISSIndexManager:
    manager: FAISSIndexManager = request.app.state.index_manager
    return manager
