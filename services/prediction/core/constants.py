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

FEATURE_DISPLAY_NAMES: dict[str, str] = {
    "entity_count_total": "Total entities in document",
    "entity_count_money": "Monetary values mentioned",
    "entity_count_peril": "Number of perils mentioned",
    "entity_count_coverage": "Coverage types mentioned",
    "entity_count_claim_status": "Claim statuses mentioned",
    "entity_count_property_type": "Property types mentioned",
    "entity_count_vehicle": "Vehicles mentioned",
    "has_open_claim": "Open claim present",
    "has_denied_claim": "Denied claim present",
    "has_fire_peril": "Fire peril present",
    "has_flood_peril": "Flood peril present",
    "has_earthquake_peril": "Earthquake peril present",
    "has_wind_peril": "Wind peril present",
    "has_cyber_coverage": "Cyber coverage requested",
    "has_umbrella_coverage": "Umbrella coverage present",
    "max_monetary_value": "Highest monetary value",
    "mean_monetary_value": "Average monetary value",
    "num_monetary_values": "Count of monetary references",
    "prior_claims_indicator": "Prior claims history",
    "property_risk_score": "Property construction risk",
    "coverage_breadth": "Breadth of coverage requested",
    "peril_diversity": "Variety of perils",
}

# Maps PROPERTY_TYPE entity text to a risk score (0 = safest, 1 = riskiest).
# Wood-frame burns easier than fire-resistive construction.
PROPERTY_RISK_MAP: dict[str, float] = {
    "fire-resistive": 0.1,
    "modified fire-resistive": 0.2,
    "non-combustible": 0.25,
    "masonry commercial": 0.3,
    "joisted masonry": 0.5,
    "steel frame": 0.4,
    "mixed-use": 0.6,
    "frame construction": 0.7,
    "wood-frame residential": 0.8,
}

DEFAULT_PROPERTY_RISK = 0.5
TOP_K_SHAP_FEATURES = 5
