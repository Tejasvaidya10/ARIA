from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from services.prediction.api.routes import limiter, router
from services.prediction.config import PredictionSettings
from services.prediction.services.predictor import create_explainer, load_model
from services.shared.health import create_health_router
from services.shared.logging import setup_logging
from services.shared.metrics import setup_metrics
from services.shared.middleware import RequestIdMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = PredictionSettings()
    setup_logging(settings.service_name, settings.log_level)

    await logger.ainfo("loading_probability_model", path=settings.xgboost_model_path)
    prob_model = load_model(settings.xgboost_model_path)

    await logger.ainfo("loading_severity_model", path=settings.xgboost_severity_model_path)
    sev_model = load_model(settings.xgboost_severity_model_path)

    await logger.ainfo("creating_shap_explainers")
    prob_explainer = create_explainer(prob_model)

    app.state.settings = settings
    app.state.probability_model = prob_model
    app.state.severity_model = sev_model
    app.state.probability_explainer = prob_explainer

    await logger.ainfo("prediction_service_ready")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ARIA Prediction Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    setup_metrics(app)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    health_router = create_health_router(
        "prediction",
        readiness_checks=[
            lambda: (
                hasattr(app.state, "probability_model") and app.state.probability_model is not None
            ),
            lambda: hasattr(app.state, "severity_model") and app.state.severity_model is not None,
        ],
    )
    app.include_router(health_router)
    app.include_router(router)

    return app


app = create_app()
