import pytest
from fastapi.testclient import TestClient

from services.llm.api.dependencies import get_provider
from services.llm.app import create_app
from services.llm.tests.conftest import FakeLLMProvider


@pytest.fixture(scope="module")
def client():  # type: ignore[no-untyped-def]
    app = create_app()
    app.dependency_overrides[get_provider] = FakeLLMProvider
    with TestClient(app) as c:
        yield c


def test_health(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "llm"


def test_ready(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/ready")
    assert resp.status_code == 200


def test_synthesize_returns_analysis(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/synthesize",
        json={
            "submission_id": "test-123",
            "entity_summary": {
                "PERIL": ["fire", "flood"],
                "MONEY": ["$50,000"],
                "COVERAGE_TYPE": ["property"],
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
    assert len(data["underwriter_narrative"]) > 0
    assert "similar_cases" in data
    assert data["processing_time_ms"] > 0


def test_synthesize_empty_entities(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/synthesize",
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
