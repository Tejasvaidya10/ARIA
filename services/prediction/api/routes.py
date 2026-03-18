import asyncio
import time

import shap
import structlog
import xgboost as xgb
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.prediction.api.dependencies import (
    get_probability_explainer,
    get_probability_model,
    get_settings,
    get_severity_model,
)
from services.prediction.config import PredictionSettings
from services.prediction.core.schemas import PredictionRequest, PredictionResponse
from services.prediction.services import feature_engineer, predictor
from services.shared.exceptions import PredictionError

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictionResponse)
@limiter.limit("20/minute")
async def predict(
    request: Request,
    body: PredictionRequest,
    settings: PredictionSettings = Depends(get_settings),
    prob_model: xgb.Booster = Depends(get_probability_model),
    sev_model: xgb.Booster = Depends(get_severity_model),
    prob_explainer: shap.TreeExplainer = Depends(get_probability_explainer),
) -> PredictionResponse | JSONResponse:
    start = time.perf_counter()

    try:
        features = feature_engineer.extract_features(body.entity_summary)
    except Exception as exc:
        await logger.awarning(
            "feature_extraction_failed", error=str(exc), submission_id=body.submission_id
        )
        return JSONResponse(
            status_code=400, content={"error": f"Feature extraction failed: {exc}"}
        )

    try:
        # XGBoost predict is CPU-bound and not thread-safe
        result = await asyncio.to_thread(
            predictor.predict_risk,
            prob_model,
            sev_model,
            prob_explainer,
            features,
            settings,
        )
    except PredictionError as exc:
        await logger.aerror("prediction_failed", error=str(exc), submission_id=body.submission_id)
        return JSONResponse(status_code=500, content={"error": "Prediction failed"})

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    result.submission_id = body.submission_id
    result.processing_time_ms = elapsed_ms

    await logger.ainfo(
        "prediction_complete",
        submission_id=result.submission_id,
        risk_tier=result.risk_tier,
        risk_probability=result.risk_probability,
        processing_time_ms=elapsed_ms,
    )
    return result
