import re

import fitz


def extract_page_text(pdf_bytes: bytes, page_number: int) -> str:
    """Extract and clean text from a single PDF page."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_number)
    raw = page.get_text("text")
    doc.close()
    return _clean_text(raw)


def extract_all_pages(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Extract text from every page. Returns list of (page_number, text)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for i in range(doc.page_count):
        raw = doc.load_page(i).get_text("text")
        pages.append((i, _clean_text(raw)))
    doc.close()
    return pages


def _clean_text(text: str) -> str:
    """Normalize whitespace from PDF extraction output."""
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
