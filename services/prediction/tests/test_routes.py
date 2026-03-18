import pytest
from fastapi.testclient import TestClient

from services.prediction.app import create_app


@pytest.fixture(scope="module")
def client():  # type: ignore[no-untyped-def]
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "prediction"


def test_ready(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/ready")
    assert resp.status_code == 200


def test_predict_with_entities(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/predict",
        json={
            "submission_id": "test-123",
            "entity_summary": {
                "PERIL": ["fire", "flood"],
                "MONEY": ["$50,000", "$500,000"],
                "COVERAGE_TYPE": ["commercial general liability"],
                "PROPERTY_TYPE": ["wood-frame residential"],
                "CLAIM_STATUS": ["pending review"],
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["submission_id"] == "test-123"
    assert data["risk_tier"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert 0.0 <= data["risk_probability"] <= 1.0
    assert data["predicted_claim_amount"] >= 0.0
    assert len(data["key_risk_factors"]) > 0
    assert data["processing_time_ms"] > 0


def test_predict_empty_entities(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/predict",
        json={
            "submission_id": "test-empty",
            "entity_summary": {},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["submission_id"] == "test-empty"


def test_metrics_endpoint(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/metrics")
    assert resp.status_code == 200
