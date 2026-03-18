import shap
import xgboost as xgb
from fastapi import Request

from services.prediction.config import PredictionSettings


def get_settings(request: Request) -> PredictionSettings:
    return request.app.state.settings  # type: ignore[no-any-return]


def get_probability_model(request: Request) -> xgb.Booster:
    return request.app.state.probability_model


def get_severity_model(request: Request) -> xgb.Booster:
    return request.app.state.severity_model


def get_probability_explainer(request: Request) -> shap.TreeExplainer:
    return request.app.state.probability_explainer
