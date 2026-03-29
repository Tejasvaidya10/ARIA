import re

import numpy as np

from services.prediction.core.constants import (
    DEFAULT_PROPERTY_RISK,
    FEATURE_NAMES,
    PROPERTY_RISK_MAP,
)


def extract_features(entity_summary: dict[str, list[str]]) -> np.ndarray:  # type: ignore[type-arg]
    """Convert NER entity summary into a feature vector for XGBoost."""
    perils = entity_summary.get("PERIL", [])
    coverages = entity_summary.get("COVERAGE_TYPE", [])
    money = entity_summary.get("MONEY", [])
    claim_statuses = entity_summary.get("CLAIM_STATUS", [])
    property_types = entity_summary.get("PROPERTY_TYPE", [])
    vehicles = entity_summary.get("VEHICLE", [])
    injuries = entity_summary.get("INJURY", [])
    incident_details = entity_summary.get("INCIDENT_DETAIL", [])

    all_count = sum(len(v) for v in entity_summary.values())
    parsed = [_parse_money(m) for m in money]
    monetary_values: list[float] = [v for v in parsed if v is not None]

    features = {
        "entity_count_total": float(all_count),
        "entity_count_money": float(len(money)),
        "entity_count_peril": float(len(perils)),
        "entity_count_coverage": float(len(coverages)),
        "entity_count_claim_status": float(len(claim_statuses)),
        "entity_count_property_type": float(len(property_types)),
        "entity_count_vehicle": float(len(vehicles)),
        "has_open_claim": _has_keyword(claim_statuses, "open"),
        "has_denied_claim": _has_keyword(claim_statuses, "denied"),
        "has_fire_peril": _has_keyword(perils, "fire"),
        "has_flood_peril": _has_keyword(perils, "flood"),
        "has_earthquake_peril": _has_keyword(perils, "earthquake"),
        "has_wind_peril": _has_keyword(perils, "wind"),
        "has_cyber_coverage": _has_keyword(coverages, "cyber"),
        "has_umbrella_coverage": _has_keyword(coverages, "umbrella"),
        "max_monetary_value": max(monetary_values) if monetary_values else 0.0,
        "mean_monetary_value": float(np.mean(monetary_values)) if monetary_values else 0.0,
        "num_monetary_values": float(len(monetary_values)),
        "prior_claims_indicator": 1.0 if claim_statuses else 0.0,
        "property_risk_score": _compute_property_risk(property_types),
        "coverage_breadth": min(len(coverages) / 10.0, 1.0),
        "peril_diversity": min(len(perils) / 8.0, 1.0),
        # v2: incident details
        "bodily_injury_count": _parse_count(injuries, "injur"),
        "vehicles_involved": _parse_count(incident_details, "vehicle"),
        "witness_count": _parse_count(incident_details, "witness"),
        "police_involved": _has_keyword(incident_details, "police"),
        "vehicle_age": _parse_vehicle_age(vehicles),
        "multi_vehicle_incident": _has_keyword(perils, "multi-vehicle"),
    }

    return np.array([features[name] for name in FEATURE_NAMES], dtype=np.float64)


def _has_keyword(entities: list[str], keyword: str) -> float:
    return 1.0 if any(keyword in e.lower() for e in entities) else 0.0


def _parse_money(text: str) -> float | None:
    """Parse a money string into millions. Returns None if unparseable."""
    for symbol in ("$", "£", "€", "¥"):
        text = text.replace(symbol, "")
    cleaned = text.replace(",", "").strip().lower()

    multiplier = 1e-6  # raw dollars → millions

    if "billion" in cleaned:
        multiplier = 1_000.0
        cleaned = cleaned.replace("billion", "").strip()
    elif "million" in cleaned:
        multiplier = 1.0
        cleaned = cleaned.replace("million", "").strip()
    elif re.search(r"\d\s*m\b", cleaned):
        multiplier = 1.0
        cleaned = re.sub(r"m\b", "", cleaned).strip()
    elif re.search(r"\d\s*k\b", cleaned):
        multiplier = 1e-3
        cleaned = re.sub(r"k\b", "", cleaned).strip()

    match = re.search(r"[\d.]+", cleaned)
    if not match:
        return None

    try:
        return float(match.group()) * multiplier
    except ValueError:
        return None


def _compute_property_risk(property_types: list[str]) -> float:
    if not property_types:
        return DEFAULT_PROPERTY_RISK
    scores = [PROPERTY_RISK_MAP.get(pt.lower(), DEFAULT_PROPERTY_RISK) for pt in property_types]
    return max(scores)


def _parse_count(entities: list[str], keyword: str) -> float:
    """Extract a numeric count from entity strings containing a keyword.

    Handles formats like "2 bodily injuries", "3 vehicles involved",
    or just "bodily injury" (defaults to 1 if keyword found but no number).
    """
    for entity in entities:
        lower = entity.lower()
        if keyword in lower:
            match = re.search(r"(\d+)", lower)
            if match:
                return float(match.group(1))
            return 1.0
    return 0.0


def _parse_vehicle_age(vehicles: list[str]) -> float:
    """Extract vehicle age from VEHICLE entities like 'Dodge Neon (2003)'.

    Returns age in years relative to 2024, or 0 if no year found.
    """
    for v in vehicles:
        match = re.search(r"\b(19|20)\d{2}\b", v)
        if match:
            year = int(match.group())
            return max(float(2024 - year), 0.0)
    return 0.0
