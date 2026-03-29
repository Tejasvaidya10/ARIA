import numpy as np
import pytest
import shap
import xgboost as xgb

from services.prediction.config import PredictionSettings
from services.prediction.core.constants import FEATURE_NAMES
from services.prediction.services.predictor import (
    classify_risk_tier,
    load_model,
    predict_risk,
)
from services.shared.schemas import RiskTier


@pytest.fixture(scope="module")
def models():  # type: ignore[no-untyped-def]
    prob_model = load_model("models/xgboost/claim_probability.json")
    sev_model = load_model("models/xgboost/claim_severity.json")
    explainer = shap.TreeExplainer(prob_model)
    return prob_model, sev_model, explainer


@pytest.fixture
def settings() -> PredictionSettings:
    return PredictionSettings()


def test_predict_risk_returns_valid_response(models, settings) -> None:  # type: ignore[no-untyped-def]
    prob_model, sev_model, explainer = models
    features = np.random.default_rng(42).random(len(FEATURE_NAMES))
    result = predict_risk(prob_model, sev_model, explainer, features, settings)

    assert 0.0 <= result.risk_probability <= 1.0
    assert result.predicted_claim_amount >= 0.0
    assert 0.0 <= result.confidence_score <= 1.0
    assert len(result.key_risk_factors) > 0
    assert result.risk_tier in list(RiskTier)


def test_risk_factors_have_direction(models, settings) -> None:  # type: ignore[no-untyped-def]
    prob_model, sev_model, explainer = models
    features = np.random.default_rng(42).random(len(FEATURE_NAMES))
    result = predict_risk(prob_model, sev_model, explainer, features, settings)

    for factor in result.key_risk_factors:
        assert factor.direction in ("increases_risk", "decreases_risk")
        assert factor.shap_value != 0.0


def test_classify_risk_tier() -> None:
    settings = PredictionSettings()
    assert classify_risk_tier(0.10, settings) == RiskTier.LOW
    assert classify_risk_tier(0.30, settings) == RiskTier.MODERATE
    assert classify_risk_tier(0.60, settings) == RiskTier.HIGH
    assert classify_risk_tier(0.80, settings) == RiskTier.CRITICAL


def test_shap_cache_hit(
    models: tuple[xgb.Booster, xgb.Booster, shap.TreeExplainer], settings: PredictionSettings
) -> None:
    from services.prediction.services.predictor import _shap_cache

    prob_model, sev_model, explainer = models
    features = np.random.default_rng(99).random(len(FEATURE_NAMES))

    _shap_cache.clear()
    predict_risk(prob_model, sev_model, explainer, features, settings)
    assert len(_shap_cache) == 1

    predict_risk(prob_model, sev_model, explainer, features, settings)
    assert len(_shap_cache) == 1


def test_load_model_missing_path() -> None:
    from services.shared.exceptions import ModelNotLoadedError

    with pytest.raises(ModelNotLoadedError):
        load_model("nonexistent/path.json")
