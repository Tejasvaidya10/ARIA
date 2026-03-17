from typing import Any

INSURANCE_ENTITY_LABELS = [
    "PERSON",
    "ORG",
    "DATE",
    "MONEY",
    "COVERAGE_TYPE",
    "PROPERTY_TYPE",
    "LOCATION",
    "PERIL",
    "POLICY_NUMBER",
    "VEHICLE",
    "CLAIM_STATUS",
]

# EntityRuler patterns for insurance-specific entities that spaCy's
# pretrained models don't recognize. Each pattern is a dict with
# "label" and "pattern" keys. "pattern" can be a string (exact match)
# or a list of token dicts for multi-token matching.

INSURANCE_PATTERNS: list[dict[str, Any]] = [
    # Coverage types
    {"label": "COVERAGE_TYPE", "pattern": "general liability"},
    {"label": "COVERAGE_TYPE", "pattern": "commercial general liability"},
    {"label": "COVERAGE_TYPE", "pattern": "professional liability"},
    {"label": "COVERAGE_TYPE", "pattern": "errors and omissions"},
    {"label": "COVERAGE_TYPE", "pattern": "workers compensation"},
    {"label": "COVERAGE_TYPE", "pattern": "workers' compensation"},
    {"label": "COVERAGE_TYPE", "pattern": "property damage"},
    {"label": "COVERAGE_TYPE", "pattern": "bodily injury"},
    {"label": "COVERAGE_TYPE", "pattern": "umbrella coverage"},
    {"label": "COVERAGE_TYPE", "pattern": "excess liability"},
    {"label": "COVERAGE_TYPE", "pattern": "commercial auto"},
    {"label": "COVERAGE_TYPE", "pattern": "inland marine"},
    {"label": "COVERAGE_TYPE", "pattern": "cyber liability"},
    {"label": "COVERAGE_TYPE", "pattern": "directors and officers"},
    {"label": "COVERAGE_TYPE", "pattern": "employment practices liability"},
    {"label": "COVERAGE_TYPE", "pattern": "business interruption"},
    {"label": "COVERAGE_TYPE", "pattern": "product liability"},
    {"label": "COVERAGE_TYPE", "pattern": "completed operations"},
    # Perils
    {"label": "PERIL", "pattern": "fire"},
    {"label": "PERIL", "pattern": "flood"},
    {"label": "PERIL", "pattern": "earthquake"},
    {"label": "PERIL", "pattern": "wind damage"},
    {"label": "PERIL", "pattern": "hail damage"},
    {"label": "PERIL", "pattern": "water damage"},
    {"label": "PERIL", "pattern": "theft"},
    {"label": "PERIL", "pattern": "vandalism"},
    {"label": "PERIL", "pattern": "lightning"},
    {"label": "PERIL", "pattern": "explosion"},
    {"label": "PERIL", "pattern": "collapse"},
    {"label": "PERIL", "pattern": "smoke damage"},
    {"label": "PERIL", "pattern": "hurricane"},
    {"label": "PERIL", "pattern": "tornado"},
    {"label": "PERIL", "pattern": "windstorm"},
    # Claim statuses
    {"label": "CLAIM_STATUS", "pattern": "open claim"},
    {"label": "CLAIM_STATUS", "pattern": "closed claim"},
    {"label": "CLAIM_STATUS", "pattern": "settled"},
    {"label": "CLAIM_STATUS", "pattern": "denied"},
    {"label": "CLAIM_STATUS", "pattern": "pending review"},
    {"label": "CLAIM_STATUS", "pattern": "under investigation"},
    {"label": "CLAIM_STATUS", "pattern": "subrogation"},
    # Property types
    {"label": "PROPERTY_TYPE", "pattern": "wood-frame residential"},
    {"label": "PROPERTY_TYPE", "pattern": "masonry commercial"},
    {"label": "PROPERTY_TYPE", "pattern": "steel frame"},
    {"label": "PROPERTY_TYPE", "pattern": "fire-resistive"},
    {"label": "PROPERTY_TYPE", "pattern": "mixed-use"},
    {"label": "PROPERTY_TYPE", "pattern": "frame construction"},
    {"label": "PROPERTY_TYPE", "pattern": "joisted masonry"},
    {"label": "PROPERTY_TYPE", "pattern": "non-combustible"},
    {"label": "PROPERTY_TYPE", "pattern": "modified fire-resistive"},
    # Policy number patterns. spaCy tokenizes "PLY-2024-00892" as
    # ["PLY-2024", "-", "00892"] so we match that token sequence.
    {
        "label": "POLICY_NUMBER",
        "pattern": [
            {"TEXT": {"REGEX": r"^[A-Z]{2,4}-\d{4}$"}},
            {"TEXT": "-"},
            {"TEXT": {"REGEX": r"^\d{3,6}$"}},
        ],
    },
]
