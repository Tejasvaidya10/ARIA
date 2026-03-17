from unittest.mock import AsyncMock

import pytest

from services.ingestion.config import IngestionSettings
from services.ingestion.services.pdf_sanitizer import validate_upload
from services.shared.exceptions import ExtractionError


def _make_upload(content: bytes, filename: str = "test.pdf") -> AsyncMock:
    mock = AsyncMock()
    mock.read.return_value = content
    mock.filename = filename
    return mock


@pytest.fixture
def settings() -> IngestionSettings:
    return IngestionSettings()


@pytest.mark.asyncio
async def test_valid_pdf_passes(sample_pdf_bytes: bytes, settings: IngestionSettings) -> None:
    upload = _make_upload(sample_pdf_bytes)
    result = await validate_upload(upload, settings)
    assert result == sample_pdf_bytes


@pytest.mark.asyncio
async def test_rejects_non_pdf(settings: IngestionSettings) -> None:
    upload = _make_upload(b"this is not a pdf")
    with pytest.raises(ExtractionError, match="not a valid PDF"):
        await validate_upload(upload, settings)


@pytest.mark.asyncio
async def test_rejects_oversized_file(sample_pdf_bytes: bytes) -> None:
    settings = IngestionSettings(max_upload_size_mb=0)
    upload = _make_upload(sample_pdf_bytes)
    with pytest.raises(ExtractionError, match="exceeds"):
        await validate_upload(upload, settings)


@pytest.mark.asyncio
async def test_rejects_corrupt_pdf(settings: IngestionSettings) -> None:
    # starts with PDF magic but body is garbage
    upload = _make_upload(b"%PDF-corrupted garbage data here")
    with pytest.raises(ExtractionError, match="corrupt"):
        await validate_upload(upload, settings)
