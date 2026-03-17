import fitz
import pytest


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Create a minimal valid PDF in memory for testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Policy Holder: John Smith\n"
        "Coverage: commercial general liability\n"
        "Premium: $50,000\n"
        "Policy Number: PLY-2024-00892\n"
        "Property: wood-frame residential at 123 Main St\n"
        "Prior Claims: fire, water damage\n"
        "Status: pending review",
    )
    content: bytes = doc.tobytes()
    doc.close()
    return content


@pytest.fixture
def empty_pdf_bytes() -> bytes:
    """A valid PDF with one page but no text."""
    doc = fitz.open()
    doc.new_page()
    content: bytes = doc.tobytes()
    doc.close()
    return content
