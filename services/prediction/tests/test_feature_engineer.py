import pytest

from services.prediction.core.constants import FEATURE_NAMES
from services.prediction.services.feature_engineer import (
    _parse_money,
    extract_features,
)


def test_feature_vector_length(sample_entity_summary: dict[str, list[str]]) -> None:
    features = extract_features(sample_entity_summary)
    assert len(features) == len(FEATURE_NAMES)


def test_entity_counts(sample_entity_summary: dict[str, list[str]]) -> None:
    features = extract_features(sample_entity_summary)
    idx = {name: i for i, name in enumerate(FEATURE_NAMES)}
    assert features[idx["entity_count_peril"]] == 2.0
    assert features[idx["entity_count_money"]] == 2.0
    assert features[idx["entity_count_coverage"]] == 2.0


def test_binary_indicators(sample_entity_summary: dict[str, list[str]]) -> None:
    features = extract_features(sample_entity_summary)
    idx = {name: i for i, name in enumerate(FEATURE_NAMES)}
    assert features[idx["has_fire_peril"]] == 1.0
    assert features[idx["has_umbrella_coverage"]] == 1.0
    assert features[idx["has_flood_peril"]] == 0.0
    assert features[idx["prior_claims_indicator"]] == 1.0


def test_property_risk_score(sample_entity_summary: dict[str, list[str]]) -> None:
    features = extract_features(sample_entity_summary)
    idx = {name: i for i, name in enumerate(FEATURE_NAMES)}
    assert features[idx["property_risk_score"]] == 0.8  # wood-frame residential


def test_monetary_parsing() -> None:
    assert _parse_money("$50,000") == pytest.approx(0.05)
    assert _parse_money("$1.5 million") == pytest.approx(1.5)
    assert _parse_money("$2 billion") == pytest.approx(2000.0)
    assert _parse_money("not a number") is None


def test_empty_summary_returns_defaults(empty_entity_summary: dict[str, list[str]]) -> None:
    features = extract_features(empty_entity_summary)
    assert len(features) == len(FEATURE_NAMES)
    assert features[0] == 0.0  # entity_count_total
    idx = {name: i for i, name in enumerate(FEATURE_NAMES)}
    assert features[idx["property_risk_score"]] == 0.5  # default
