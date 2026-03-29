from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.integration.helpers import PassthroughProvider, ServiceRouter


@pytest.fixture(scope="module")
def prediction_client() -> Iterator[TestClient]:
    from services.prediction.app import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture(scope="module")
def rag_client() -> Iterator[TestClient]:
    from services.rag.app import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture(scope="module")
def routed_llm_client(
    prediction_client: TestClient,
    rag_client: TestClient,
) -> Iterator[TestClient]:
    from services.llm.api.dependencies import get_http_client, get_provider
    from services.llm.app import create_app

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
        yield c
