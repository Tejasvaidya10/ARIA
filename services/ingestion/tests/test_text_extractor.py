from services.ingestion.services.text_extractor import extract_all_pages, extract_page_text


def test_extract_page_text(sample_pdf_bytes: bytes) -> None:
    text = extract_page_text(sample_pdf_bytes, 0)
    assert "John Smith" in text
    assert "commercial general liability" in text


def test_extract_all_pages(sample_pdf_bytes: bytes) -> None:
    pages = extract_all_pages(sample_pdf_bytes)
    assert len(pages) == 1
    page_num, text = pages[0]
    assert page_num == 0
    assert "$50,000" in text


def test_empty_page_returns_empty_string(empty_pdf_bytes: bytes) -> None:
    text = extract_page_text(empty_pdf_bytes, 0)
    assert text == ""
