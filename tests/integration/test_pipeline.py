import httpx
from fastapi.testclient import TestClient

from tests.integration.helpers import FIRE_SUBMISSION, PassthroughProvider


def test_prediction_fire_submission(prediction_client: TestClient) -> None:
    resp = prediction_client.post(
        "/predict",
        json={"submission_id": "int-test-1", "entity_summary": FIRE_SUBMISSION},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_tier"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert 0.0 <= data["risk_probability"] <= 1.0
    assert isinstance(data["key_risk_factors"], list)
    assert data["predicted_claim_amount"] >= 0.0


def test_rag_returns_similar_cases(rag_client: TestClient) -> None:
    resp = rag_client.post(
        "/search",
        json={"entity_summary": FIRE_SUBMISSION},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["results"], list)
    assert data["total_indexed"] > 0
    if data["results"]:
        assert 0.0 <= data["results"][0]["similarity_score"] <= 1.0
        assert "policy_id" in data["results"][0]


def test_full_pipeline_synthesizes_narrative(routed_llm_client: TestClient) -> None:
    resp = routed_llm_client.post(
        "/synthesize",
        json={
            "submission_id": "int-test-pipeline-1",
            "entity_summary": FIRE_SUBMISSION,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["submission_id"] == "int-test-pipeline-1"
    assert data["risk_tier"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert 0.0 <= data["risk_probability"] <= 1.0
    assert isinstance(data["similar_cases"], list)
    assert len(data["underwriter_narrative"]) > 0
    assert data["processing_time_ms"] > 0


def test_pipeline_prediction_fallback(rag_client: TestClient) -> None:
    """Prediction service returns 404 (non-retryable) — LLM falls back gracefully."""

    class PredictionDown(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if ":8001" in str(request.url):
                return httpx.Response(404, content=b'{"error": "not found"}')
            resp = rag_client.request(
                method=request.method,
                url=request.url.path,
                content=request.content,
                headers=dict(request.headers),
            )
            return httpx.Response(
                status_code=resp.status_code,
                headers=dict(resp.headers),
                content=resp.content,
            )

    from services.llm.api.dependencies import get_http_client, get_provider
    from services.llm.app import create_app

    transport = PredictionDown()
    routed_http_client = httpx.AsyncClient(transport=transport)

    app = create_app()
    app.dependency_overrides[get_provider] = lambda: PassthroughProvider()
    app.dependency_overrides[get_http_client] = lambda: routed_http_client

    with TestClient(app) as c:
        resp = c.post(
            "/synthesize",
            json={"submission_id": "fallback-test", "entity_summary": FIRE_SUBMISSION},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_tier"] == "MODERATE"
    assert data["risk_probability"] == 0.5


def test_request_id_propagates(
    prediction_client: TestClient,
    rag_client: TestClient,
) -> None:
    """X-Request-ID sent to LLM must appear in headers forwarded to prediction."""
    from services.llm.api.dependencies import get_http_client, get_provider
    from services.llm.app import create_app
    from tests.integration.helpers import ServiceRouter

    router = ServiceRouter(
        {
            "http://localhost:8001": prediction_client,
            "http://localhost:8002": rag_client,
        }
    )
    routed_http_client = httpx.AsyncClient(transport=router)

    app = create_app()
    app.dependency_overrides[get_provider] = lambda: PassthroughProvider()
    app.dependency_overrides[get_http_client] = lambda: routed_http_client

    with TestClient(app) as c:
        c.post(
            "/synthesize",
            json={"submission_id": "req-id-test", "entity_summary": FIRE_SUBMISSION},
            headers={"X-Request-ID": "integration-test-123"},
        )

    assert "x-request-id" in router.last_request_headers
    assert router.last_request_headers["x-request-id"] == "integration-test-123"
