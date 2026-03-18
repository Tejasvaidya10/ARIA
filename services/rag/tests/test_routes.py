import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from services.rag.app import create_app

# Build the app once with a test-friendly setup.
# The lifespan loads the embedding model and FAISS index.
# If no index files exist on disk, the service starts with an empty index
# (which is fine -- search just returns no results).


@pytest.fixture()
def app() -> FastAPI:
    return create_app()


@pytest.mark.asyncio
async def test_health(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "rag"


@pytest.mark.asyncio
async def test_ready(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ready")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_search_returns_response(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
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


@pytest.mark.asyncio
async def test_search_empty_entities(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/search",
            json={"entity_summary": {}, "top_k": 5},
        )
    assert resp.status_code == 200
    assert resp.json()["query_text"] == "empty submission"


@pytest.mark.asyncio
async def test_metrics_endpoint(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/metrics")
    assert resp.status_code == 200
