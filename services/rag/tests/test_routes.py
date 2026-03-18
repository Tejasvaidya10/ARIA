import pytest
from fastapi.testclient import TestClient

from services.rag.app import create_app

# The lifespan loads the embedding model and FAISS index.
# If no index files exist on disk, the service starts with an empty index
# (which is fine -- search just returns no results).


@pytest.fixture(scope="module")
def client():  # type: ignore[no-untyped-def]
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "rag"


def test_ready(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/ready")
    assert resp.status_code == 200


def test_search_returns_response(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/search",
        json={
            "entity_summary": {
                "PERIL": ["fire"],
                "COVERAGE_TYPE": ["property"],
            },
            "top_k": 3,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "total_indexed" in data
    assert "query_text" in data


def test_search_empty_entities(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/search",
        json={"entity_summary": {}, "top_k": 5},
    )
    assert resp.status_code == 200
    assert resp.json()["query_text"] == "empty submission"


def test_metrics_endpoint(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/metrics")
    assert resp.status_code == 200
