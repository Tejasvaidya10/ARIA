from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from services.rag.api.routes import limiter, router
from services.rag.config import RAGSettings
from services.rag.services.embedder import load_embedding_model
from services.rag.services.index_manager import FAISSIndexManager
from services.shared.health import create_health_router
from services.shared.logging import setup_logging
from services.shared.metrics import setup_metrics
from services.shared.middleware import RequestIdMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = RAGSettings()
    setup_logging(settings.service_name, settings.log_level)

    await logger.ainfo("loading_embedding_model", model=settings.embedding_model)
    model = load_embedding_model(settings.embedding_model)

    await logger.ainfo("loading_faiss_index", path=settings.index_path)
    dim: int = model.get_sentence_embedding_dimension()  # type: ignore[assignment]
    manager = FAISSIndexManager(dimension=dim)
    manager.load(settings.index_path, settings.case_store_path)
    await logger.ainfo("index_loaded", total_vectors=manager.total_indexed)

    app.state.settings = settings
    app.state.embedding_model = model
    app.state.index_manager = manager

    await logger.ainfo("rag_service_ready")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ARIA RAG Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    setup_metrics(app)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    health_router = create_health_router(
        "rag",
        readiness_checks=[
            lambda: hasattr(app.state, "index_manager") and app.state.index_manager is not None,
            lambda: (
                hasattr(app.state, "embedding_model") and app.state.embedding_model is not None
            ),
        ],
    )
    app.include_router(health_router)
    app.include_router(router)

    return app


app = create_app()
