from pathlib import Path

import numpy as np
import shap
import xgboost as xgb
from prometheus_client import Counter

from services.prediction.config import PredictionSettings
from services.prediction.core.constants import (
    FEATURE_DISPLAY_NAMES,
    FEATURE_NAMES,
    TOP_K_SHAP_FEATURES,
)
from services.prediction.core.schemas import PredictionResponse
from services.shared.exceptions import ModelNotLoadedError
from services.shared.schemas import RiskFactor, RiskTier

_shap_cache: dict[bytes, list[RiskFactor]] = {}
_SHAP_CACHE_MAX = 512

_risk_tier_counter = Counter(
    "aria_risk_tier_total",
    "Number of predictions by risk tier",
    ["tier"],
)
_shap_cache_hits = Counter("aria_shap_cache_hits_total", "SHAP explanation cache hits")
_shap_cache_misses = Counter("aria_shap_cache_misses_total", "SHAP explanation cache misses")


def load_model(path: str) -> xgb.Booster:
    if not Path(path).exists():
        raise ModelNotLoadedError(f"Model not found at {path}")
    model = xgb.Booster()
    model.load_model(path)
    return model


def create_explainer(model: xgb.Booster) -> shap.TreeExplainer:
    return shap.TreeExplainer(model)


def _get_shap_factors(explainer: shap.TreeExplainer, features: np.ndarray) -> list[RiskFactor]:  # type: ignore[type-arg]
    key = features.tobytes()
    if key in _shap_cache:
        _shap_cache_hits.inc()
        return _shap_cache[key]

    dmatrix = xgb.DMatrix(features.reshape(1, -1), feature_names=FEATURE_NAMES)
    shap_values = explainer.shap_values(dmatrix)
    factors = _extract_risk_factors(shap_values[0])

    if len(_shap_cache) >= _SHAP_CACHE_MAX:
        _shap_cache.pop(next(iter(_shap_cache)))
    _shap_cache[key] = factors
    _shap_cache_misses.inc()
    return factors


def predict_risk(
    probability_model: xgb.Booster,
    severity_model: xgb.Booster,
    probability_explainer: shap.TreeExplainer,
    features: np.ndarray,  # type: ignore[type-arg]
    settings: PredictionSettings,
) -> PredictionResponse:
    dmatrix = xgb.DMatrix(
        features.reshape(1, -1),
        feature_names=FEATURE_NAMES,
    )

    risk_probability = float(probability_model.predict(dmatrix)[0])
    predicted_amount = float(severity_model.predict(dmatrix)[0])
    predicted_amount = max(predicted_amount, 0.0)

    risk_factors = _get_shap_factors(probability_explainer, features)
    risk_tier = classify_risk_tier(risk_probability, settings)
    _risk_tier_counter.labels(tier=risk_tier.value).inc()
    confidence = abs(risk_probability - 0.5) * 2

    return PredictionResponse(
        submission_id="",  # filled by the route handler
        risk_tier=risk_tier,
        risk_probability=round(risk_probability, 4),
        predicted_claim_amount=round(predicted_amount, 2),
        key_risk_factors=risk_factors,
        confidence_score=round(confidence, 4),
        processing_time_ms=0.0,  # filled by the route handler
    )


def classify_risk_tier(probability: float, settings: PredictionSettings) -> RiskTier:
    if probability < settings.risk_threshold_low:
        return RiskTier.LOW
    if probability < settings.risk_threshold_moderate:
        return RiskTier.MODERATE
    if probability < settings.risk_threshold_high:
        return RiskTier.HIGH
    return RiskTier.CRITICAL


def _extract_risk_factors(shap_values: np.ndarray) -> list[RiskFactor]:  # type: ignore[type-arg]
    """Pick the top-k features by absolute SHAP value."""
    abs_values = np.abs(shap_values)
    top_indices = np.argsort(abs_values)[::-1][:TOP_K_SHAP_FEATURES]

    factors = []
    for idx in top_indices:
        val = float(shap_values[idx])
        if abs(val) < 1e-6:
            continue
        name = FEATURE_NAMES[idx]
        factors.append(
            RiskFactor(
                name=FEATURE_DISPLAY_NAMES.get(name, name),
                shap_value=round(val, 6),
                direction="increases_risk" if val > 0 else "decreases_risk",
            )
        )
    return factors
