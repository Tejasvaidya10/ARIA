from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from services.ingestion.api.routes import limiter, router
from services.ingestion.config import IngestionSettings
from services.ingestion.core.constants import INSURANCE_PATTERNS
from services.ingestion.services import ner_extractor
from services.ingestion.services.spark_pipeline import create_spark_session
from services.shared.health import create_health_router
from services.shared.logging import setup_logging
from services.shared.metrics import setup_metrics
from services.shared.middleware import RequestIdMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = IngestionSettings()
    setup_logging(settings.service_name, settings.log_level)

    await logger.ainfo("starting_spark_session")
    spark = create_spark_session(settings)

    await logger.ainfo("loading_spacy_pipeline", model=settings.spacy_model_path)
    nlp = ner_extractor.load_nlp_pipeline(settings.spacy_model_path, INSURANCE_PATTERNS)

    app.state.settings = settings
    app.state.spark = spark
    app.state.nlp = nlp

    await logger.ainfo("ingestion_service_ready")
    yield

    await logger.ainfo("shutting_down_spark")
    spark.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="ARIA Ingestion Service",
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
        "ingestion",
        readiness_checks=[
            lambda: hasattr(app.state, "spark") and app.state.spark is not None,
            lambda: hasattr(app.state, "nlp") and app.state.nlp is not None,
        ],
    )
    app.include_router(health_router)
    app.include_router(router)

    return app


app = create_app()
