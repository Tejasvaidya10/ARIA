import httpx
import pytest
from fastapi.testclient import TestClient

from services.llm.api.dependencies import get_provider, get_settings
from services.llm.app import create_app
from services.llm.config import LLMSettings
from services.llm.tests.conftest import FakeLLMProvider
from services.shared.schemas import HallucinationCheck


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


def test_synthesize_hallucination_check_off(client: TestClient) -> None:
    resp = client.post(
        "/synthesize",
        json={"submission_id": "hall-off", "entity_summary": {"PERIL": ["fire"]}},
    )
    assert resp.status_code == 200
    assert resp.json()["hallucination_check"] is None


def test_synthesize_hallucination_check_on(monkeypatch: pytest.MonkeyPatch) -> None:
    canned = HallucinationCheck(detected=False, count=0, flags=[], confidence=0.95)

    async def fake_check(*args: object, **kwargs: object) -> HallucinationCheck:
        return canned

    monkeypatch.setattr("services.llm.api.routes.detect_hallucinations", fake_check)

    def override_settings() -> LLMSettings:
        s = LLMSettings()
        s.enable_hallucination_check = True
        s.anthropic_api_key = "test-key"
        return s

    app = create_app()
    app.dependency_overrides[get_provider] = FakeLLMProvider
    app.dependency_overrides[get_settings] = override_settings

    with TestClient(app) as c:
        resp = c.post(
            "/synthesize",
            json={"submission_id": "hall-on", "entity_summary": {"PERIL": ["fire"]}},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["hallucination_check"] is not None
    assert data["hallucination_check"]["detected"] is False
    assert data["hallucination_check"]["confidence"] == pytest.approx(0.95)


def test_http_client_has_structured_timeout(client: TestClient) -> None:
    timeout = client.app.state.http_client.timeout
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.connect == 3.0
    assert timeout.read == 10.0
