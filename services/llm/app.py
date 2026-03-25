from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from services.llm.api.routes import limiter, router
from services.llm.config import LLMSettings
from services.llm.services.orchestrator import get_provider
from services.shared.health import create_health_router
from services.shared.logging import setup_logging
from services.shared.metrics import setup_metrics
from services.shared.middleware import RequestIdMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = LLMSettings()
    setup_logging(settings.service_name, settings.log_level)

    await logger.ainfo("creating_llm_provider", provider=settings.provider)
    provider = get_provider(settings)

    await logger.ainfo("creating_http_client", timeout=settings.request_timeout)
    http_client = httpx.AsyncClient(timeout=settings.request_timeout)

    app.state.settings = settings
    app.state.provider = provider
    app.state.http_client = http_client

    await logger.ainfo("llm_service_ready", provider=settings.provider)
    yield

    await http_client.aclose()
    await logger.ainfo("http_client_closed")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ARIA LLM Synthesis Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)
    setup_metrics(app)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    health_router = create_health_router(
        "llm",
        readiness_checks=[
            lambda: hasattr(app.state, "provider") and app.state.provider is not None,
        ],
    )
    app.include_router(health_router)
    app.include_router(router)

    return app


app = create_app()
