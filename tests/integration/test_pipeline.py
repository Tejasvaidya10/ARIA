from fastapi.testclient import TestClient

from tests.integration.helpers import FIRE_SUBMISSION


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
