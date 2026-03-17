import pytest
from fastapi.testclient import TestClient

from services.ingestion.app import create_app


@pytest.fixture(scope="module")
def client():  # type: ignore[no-untyped-def]
    """Create a test client with real Spark and spaCy instances.

    scope=module so we only boot Spark once across all tests in this file.
    """
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "ingestion"


def test_ready(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/ready")
    assert resp.status_code == 200


def test_extract_valid_pdf(client, sample_pdf_bytes: bytes) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/extract",
        files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "test.pdf"
    assert data["page_count"] == 1
    assert len(data["entities"]) > 0
    assert "entity_summary" in data


def test_extract_rejects_non_pdf(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/extract",
        files={"file": ("bad.pdf", b"not a pdf", "application/pdf")},
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_metrics_endpoint(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/metrics")
    assert resp.status_code == 200
