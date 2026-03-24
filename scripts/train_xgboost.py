"""Train XGBoost models on real Kaggle Auto Insurance Claims data.

Reads data/raw/insurance_claims.csv (Kaggle: buntyshah/auto-insurance-claims-data),
converts each row into an NER-style entity summary, runs it through the same
feature_engineer used at inference time, and trains two models:

  models/xgboost/claim_probability.json  (binary: will a claim be high-cost?)
  models/xgboost/claim_severity.json     (regression: total claim amount in $)

This ensures the models train on features shaped exactly like what the prediction
service sees in production when processing real NER output from PDFs.

Usage:
    python -m scripts.train_xgboost
"""

import csv
from pathlib import Path

import numpy as np
import xgboost as xgb
from sklearn.metrics import roc_auc_score

from services.prediction.core.constants import FEATURE_NAMES
from services.prediction.services.feature_engineer import extract_features

DATA_PATH = Path("data/raw/insurance_claims.csv")
OUTPUT_DIR = Path("models/xgboost")

# Incident types map to "perils" the NER pipeline would extract
INCIDENT_TO_PERILS = {
    "Single Vehicle Collision": ["collision"],
    "Vehicle Theft": ["theft"],
    "Multi-vehicle Collision": ["collision", "multi-vehicle"],
    "Parked Car": ["vandalism"],
}


def row_to_entity_summary(row: dict[str, str]) -> dict[str, list[str]]:
    """Convert a CSV row into the entity summary format NER would produce.

    Only uses pre-claim information — nothing derived from incident_severity
    (the target variable) to avoid data leakage.
    """
    entities: dict[str, list[str]] = {}

    # Perils from incident type
    incident_type = row.get("incident_type", "")
    perils = INCIDENT_TO_PERILS.get(incident_type, [])
    if row.get("property_damage", "").upper() == "YES":
        perils = [*perils, "property damage"]
    if perils:
        entities["PERIL"] = perils

    # Coverage info from policy fields
    coverages = []
    csl = row.get("policy_csl", "")
    if csl:
        coverages.append(f"CSL {csl}")
    deductible = row.get("policy_deductable", "")
    if deductible and deductible != "?":
        coverages.append(f"deductible ${deductible}")
    umbrella = int(row.get("umbrella_limit", "0") or "0")
    if umbrella > 0:
        coverages.append(f"umbrella ${umbrella:,}")
    if coverages:
        entities["COVERAGE_TYPE"] = coverages

    # Money values — only include info available BEFORE the claim outcome.
    # total_claim_amount is the target, so including it would be data leakage.
    money = []
    premium = row.get("policy_annual_premium", "")
    if premium and premium != "?":
        money.append(f"${float(premium):,.2f}")
    capital_gains = row.get("capital-gains", "")
    if capital_gains and capital_gains != "?" and float(capital_gains) > 0:
        money.append(f"${float(capital_gains):,.0f}")
    if money:
        entities["MONEY"] = money

    # Vehicle with year for age calculation
    make = row.get("auto_make", "")
    model = row.get("auto_model", "")
    year = row.get("auto_year", "")
    if make:
        vehicle_str = f"{make} {model}".strip()
        if year:
            vehicle_str += f" ({year})"
        entities["VEHICLE"] = [vehicle_str]

    # Injury information — would appear in any incident report
    injuries = row.get("bodily_injuries", "0")
    if injuries and injuries != "?" and int(injuries) > 0:
        entities["INJURY"] = [f"{injuries} bodily injuries"]

    # Incident details — facts a claims adjuster or NER pipeline would extract
    details = []
    num_vehicles = row.get("number_of_vehicles_involved", "1")
    if num_vehicles and num_vehicles != "?" and int(num_vehicles) > 1:
        details.append(f"{num_vehicles} vehicles involved")
    witnesses = row.get("witnesses", "0")
    if witnesses and witnesses != "?" and int(witnesses) > 0:
        details.append(f"{witnesses} witnesses")
    authority = row.get("authorities_contacted", "")
    if authority and authority.lower() in ("police", "fire", "ambulance"):
        details.append(f"{authority.lower()} contacted")
    if details:
        entities["INCIDENT_DETAIL"] = details

    return entities


# Map incident_severity to a binary target.
# HIGH risk = Major Damage or Total Loss (would be scored HIGH/CRITICAL).
# LOW risk = Trivial Damage or Minor Damage (would be scored LOW/MODERATE).
SEVERITY_TO_RISK = {
    "Trivial Damage": 0.0,
    "Minor Damage": 0.0,
    "Major Damage": 1.0,
    "Total Loss": 1.0,
}


def load_kaggle_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load real insurance claims and convert to feature vectors."""
    features_list = []
    y_cls_list = []
    y_sev_list = []

    with open(DATA_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_summary = row_to_entity_summary(row)
            feature_vec = extract_features(entity_summary)
            features_list.append(feature_vec)

            # Classification target: is this a severe incident?
            # Based on incident_severity directly, not dollar amounts.
            severity = row.get("incident_severity", "")
            y_cls_list.append(SEVERITY_TO_RISK.get(severity, 0.0))

            total_claim = float(row.get("total_claim_amount", "0") or "0")
            y_sev_list.append(total_claim)

    features = np.array(features_list)
    y_cls = np.array(y_cls_list)
    y_sev = np.array(y_sev_list)

    high_risk = int(y_cls.sum())
    print(f"  high-risk samples (Major/Total Loss): {high_risk} ({high_risk / len(y_cls):.1%})")
    print(f"  low-risk samples (Trivial/Minor): {len(y_cls) - high_risk}")

    return features, y_cls, y_sev


def train_models(features: np.ndarray, y_cls: np.ndarray, y_sev: np.ndarray) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    n = len(features)
    split = int(n * 0.8)
    idx = np.arange(n)
    np.random.default_rng(42).shuffle(idx)
    train_idx, test_idx = idx[:split], idx[split:]

    # --- Classification model (high-cost claim prediction) ---
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
    model_cls = xgb.train(cls_params, dtrain, num_boost_round=200, verbose_eval=False)

    preds = model_cls.predict(dtest)
    auc = roc_auc_score(y_cls[test_idx], preds)
    print(f"  classification AUC: {auc:.4f}")

    cls_path = OUTPUT_DIR / "claim_probability.json"
    model_cls.save_model(str(cls_path))
    print(f"  saved: {cls_path}")

    # --- Severity model (total claim amount regression) ---
    dtrain_sev = xgb.DMatrix(
        features[train_idx], label=y_sev[train_idx], feature_names=FEATURE_NAMES
    )
    dtest_sev = xgb.DMatrix(features[test_idx], label=y_sev[test_idx], feature_names=FEATURE_NAMES)

    sev_params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "max_depth": 6,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "seed": 42,
    }
    model_sev = xgb.train(sev_params, dtrain_sev, num_boost_round=200, verbose_eval=False)

    sev_preds = model_sev.predict(dtest_sev)
    rmse = np.sqrt(np.mean((y_sev[test_idx] - sev_preds) ** 2))
    mae = np.mean(np.abs(y_sev[test_idx] - sev_preds))
    print(f"  severity RMSE: ${rmse:,.0f}")
    print(f"  severity MAE: ${mae:,.0f}")

    sev_path = OUTPUT_DIR / "claim_severity.json"
    model_sev.save_model(str(sev_path))
    print(f"  saved: {sev_path}")

    # Validate SHAP works
    import shap

    explainer = shap.TreeExplainer(model_cls)
    sample = dtest.slice([0])
    shap_values = explainer.shap_values(sample)
    top_idx = int(np.argmax(np.abs(shap_values[0])))
    print(f"  SHAP validation passed. Top feature: {FEATURE_NAMES[top_idx]}")


if __name__ == "__main__":
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found.")
        print(
            "Download it first: kaggle datasets download -d buntyshah/auto-insurance-claims-data -p data/raw/ --unzip"
        )
        raise SystemExit(1)

    print("Loading Kaggle Auto Insurance Claims data...")
    features, y_cls, y_sev = load_kaggle_data()
    print(f"  loaded {len(features)} claims, {len(FEATURE_NAMES)} features")
    print("Training XGBoost models on real data...")
    train_models(features, y_cls, y_sev)
    print("Done.")
