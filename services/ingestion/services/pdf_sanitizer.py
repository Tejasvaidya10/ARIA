import fitz
from fastapi import UploadFile

from services.ingestion.config import IngestionSettings
from services.shared.exceptions import ExtractionError

PDF_MAGIC_BYTES = b"%PDF-"


async def validate_upload(file: UploadFile, settings: IngestionSettings) -> bytes:
    """Validate and sanitize an uploaded PDF before processing.

    Checks file size, PDF magic bytes, structural integrity via PyMuPDF,
    and page count limits. Returns raw bytes if all checks pass.
    """
    content = await file.read()

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ExtractionError(
            f"File exceeds {settings.max_upload_size_mb}MB limit "
            f"({len(content) / 1024 / 1024:.1f}MB)"
        )

    if not content[:5] == PDF_MAGIC_BYTES:
        raise ExtractionError("File is not a valid PDF (bad magic bytes)")

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise ExtractionError(f"PDF is corrupt or unreadable: {exc}") from exc

    if doc.page_count == 0:
        doc.close()
        raise ExtractionError("PDF has no pages")

    if doc.page_count > settings.max_pages:
        doc.close()
        raise ExtractionError(f"PDF has {doc.page_count} pages (limit: {settings.max_pages})")

    doc.close()
    return content
