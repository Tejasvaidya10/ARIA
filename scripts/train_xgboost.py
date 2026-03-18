"""Generate synthetic insurance data and train XGBoost models for ARIA.

Produces two model artifacts:
  models/xgboost/claim_probability.json  (binary classification)
  models/xgboost/claim_severity.json     (regression, dollar amount)

Run from the repo root:
  python scripts/train_xgboost.py
"""

from pathlib import Path

import numpy as np
import xgboost as xgb
from sklearn.metrics import roc_auc_score

FEATURE_NAMES = [
    "entity_count_total",
    "entity_count_money",
    "entity_count_peril",
    "entity_count_coverage",
    "entity_count_claim_status",
    "entity_count_property_type",
    "entity_count_vehicle",
    "has_open_claim",
    "has_denied_claim",
    "has_fire_peril",
    "has_flood_peril",
    "has_earthquake_peril",
    "has_wind_peril",
    "has_cyber_coverage",
    "has_umbrella_coverage",
    "max_monetary_value",
    "mean_monetary_value",
    "num_monetary_values",
    "prior_claims_indicator",
    "property_risk_score",
    "coverage_breadth",
    "peril_diversity",
]

OUTPUT_DIR = Path("models/xgboost")


def generate_synthetic_data(
    n_samples: int = 5000, seed: int = 42
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)

    # Entity counts (Poisson-distributed)
    entity_count_peril = rng.poisson(1.5, n_samples).astype(float)
    entity_count_coverage = rng.poisson(2.0, n_samples).astype(float)
    entity_count_money = rng.poisson(2.0, n_samples).astype(float)
    entity_count_claim_status = rng.poisson(0.5, n_samples).astype(float)
    entity_count_property_type = rng.poisson(1.0, n_samples).astype(float)
    entity_count_vehicle = rng.poisson(0.3, n_samples).astype(float)
    entity_count_total = (
        entity_count_peril
        + entity_count_coverage
        + entity_count_money
        + entity_count_claim_status
        + entity_count_property_type
        + entity_count_vehicle
        + rng.poisson(4, n_samples)  # other entities (PERSON, ORG, DATE, etc.)
    ).astype(float)

    # Binary indicators
    has_open_claim = rng.binomial(1, 0.15, n_samples).astype(float)
    has_denied_claim = rng.binomial(1, 0.08, n_samples).astype(float)
    has_fire_peril = rng.binomial(1, 0.20, n_samples).astype(float)
    has_flood_peril = rng.binomial(1, 0.12, n_samples).astype(float)
    has_earthquake_peril = rng.binomial(1, 0.05, n_samples).astype(float)
    has_wind_peril = rng.binomial(1, 0.18, n_samples).astype(float)
    has_cyber_coverage = rng.binomial(1, 0.10, n_samples).astype(float)
    has_umbrella_coverage = rng.binomial(1, 0.25, n_samples).astype(float)

    # Monetary features (in millions)
    max_monetary_value = rng.lognormal(-0.5, 1.2, n_samples)
    mean_monetary_value = max_monetary_value * rng.uniform(0.3, 0.9, n_samples)
    num_monetary_values = entity_count_money

    # Derived features
    prior_claims_indicator = (entity_count_claim_status > 0).astype(float)
    property_risk_score = rng.beta(2, 5, n_samples)
    coverage_breadth = np.clip(entity_count_coverage / 10, 0, 1)
    peril_diversity = np.clip(entity_count_peril / 8, 0, 1)

    features = np.column_stack(
        [
            entity_count_total,
            entity_count_money,
            entity_count_peril,
            entity_count_coverage,
            entity_count_claim_status,
            entity_count_property_type,
            entity_count_vehicle,
            has_open_claim,
            has_denied_claim,
            has_fire_peril,
            has_flood_peril,
            has_earthquake_peril,
            has_wind_peril,
            has_cyber_coverage,
            has_umbrella_coverage,
            max_monetary_value,
            mean_monetary_value,
            num_monetary_values,
            prior_claims_indicator,
            property_risk_score,
            coverage_breadth,
            peril_diversity,
        ]
    )

    # Generate claim probability from a latent risk score
    latent_risk = (
        0.3 * has_fire_peril
        + 0.25 * has_flood_peril
        + 0.35 * has_earthquake_peril
        + 0.2 * has_wind_peril
        + 0.4 * prior_claims_indicator
        + 0.3 * has_open_claim
        + 0.15 * has_denied_claim
        + 0.2 * property_risk_score
        + 0.15 * peril_diversity
        + 0.1 * np.clip(max_monetary_value, 0, 5)
        - 0.15 * has_umbrella_coverage
        - 0.8  # bias term to center the distribution
        + rng.normal(0, 0.3, n_samples)
    )
    claim_prob = 1 / (1 + np.exp(-latent_risk))
    y_cls = rng.binomial(1, claim_prob).astype(float)

    # Severity target (only meaningful for positive claims)
    base_severity = max_monetary_value * 50_000 + 10_000
    severity_mult = (
        1.0
        + 0.5 * has_fire_peril
        + 0.3 * has_flood_peril
        + 0.8 * has_earthquake_peril
        + 0.2 * property_risk_score
    )
    y_sev = base_severity * severity_mult * rng.lognormal(0, 0.3, n_samples)
    y_sev = y_sev * y_cls  # zero for non-claims

    return features, y_cls, y_sev


def train_models(features: np.ndarray, y_cls: np.ndarray, y_sev: np.ndarray) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Split train/test
    n = len(features)
    split = int(n * 0.8)
    idx = np.arange(n)
    np.random.default_rng(42).shuffle(idx)
    train_idx, test_idx = idx[:split], idx[split:]

    # --- Classification model ---
    dtrain = xgb.DMatrix(features[train_idx], label=y_cls[train_idx], feature_names=FEATURE_NAMES)
    dtest = xgb.DMatrix(features[test_idx], label=y_cls[test_idx], feature_names=FEATURE_NAMES)

    cls_params = {
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "max_depth": 6,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "seed": 42,
    }
    model_cls = xgb.train(cls_params, dtrain, num_boost_round=100, verbose_eval=False)

    preds = model_cls.predict(dtest)
    auc = roc_auc_score(y_cls[test_idx], preds)
    print(f"Classification model AUC: {auc:.4f}")

    cls_path = OUTPUT_DIR / "claim_probability.json"
    model_cls.save_model(str(cls_path))
    print(f"Saved: {cls_path}")

    # --- Severity model (train only on positive claims) ---
    pos_train = train_idx[y_cls[train_idx] > 0]
    pos_test = test_idx[y_cls[test_idx] > 0]

    if len(pos_train) < 10:
        print("Not enough positive samples for severity model")
        return

    dtrain_sev = xgb.DMatrix(
        features[pos_train], label=y_sev[pos_train], feature_names=FEATURE_NAMES
    )
    dtest_sev = xgb.DMatrix(features[pos_test], label=y_sev[pos_test], feature_names=FEATURE_NAMES)

    sev_params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "max_depth": 6,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "seed": 42,
    }
    model_sev = xgb.train(sev_params, dtrain_sev, num_boost_round=100, verbose_eval=False)

    sev_preds = model_sev.predict(dtest_sev)
    rmse = np.sqrt(np.mean((y_sev[pos_test] - sev_preds) ** 2))
    print(f"Severity model RMSE: ${rmse:,.0f}")

    sev_path = OUTPUT_DIR / "claim_severity.json"
    model_sev.save_model(str(sev_path))
    print(f"Saved: {sev_path}")

    # Validate SHAP works
    import shap

    explainer = shap.TreeExplainer(model_cls)
    sample = dtest.slice([0])
    shap_values = explainer.shap_values(sample)
    top_feature_idx = int(np.argmax(np.abs(shap_values[0])))
    print(f"SHAP validation passed. Top feature: {FEATURE_NAMES[top_feature_idx]}")


if __name__ == "__main__":
    print("Generating synthetic insurance data...")
    features, y_cls, y_sev = generate_synthetic_data()
    print(
        f"Generated {len(features)} samples, {int(y_cls.sum())} positive claims ({y_cls.mean():.1%})"
    )
    print("Training XGBoost models...")
    train_models(features, y_cls, y_sev)
    print("Done.")
