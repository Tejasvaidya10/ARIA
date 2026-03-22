"""Download SEC EDGAR 10-K Risk Factors from major insurance companies.

Fetches annual filings, extracts the "Item 1A - Risk Factors" section,
cleans the HTML, and saves as plain text files for downstream use in
the RAG index and NER testing.

SEC EDGAR requires a User-Agent header with contact info. No API key needed.

Usage:
    python -m scripts.download_edgar
"""

import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

# Major insurance companies and their CIK numbers
INSURERS = {
    "AIG": "0000005272",
    "Travelers": "0000086312",
    "Allstate": "0000899629",
    "Progressive": "0000080661",
    "Chubb": "0000896159",
    "MetLife": "0001099219",
    "Hartford": "0000874766",
    "Markel": "0001096343",
}

USER_AGENT = "ARIA tejas tvaidya@student.gsu.edu"
OUTPUT_DIR = Path("data/edgar")
SEC_BASE = "https://data.sec.gov"
ARCHIVE_BASE = "https://www.sec.gov/Archives/edgar/data"


def fetch(url: str) -> str:
    """Fetch a URL with the required SEC User-Agent header."""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_latest_10k(cik: str) -> tuple[str, str, str] | None:
    """Find the most recent 10-K filing for a company.

    Returns (accession_number, primary_doc, filing_date) or None.
    """
    import json

    url = f"{SEC_BASE}/submissions/CIK{cik}.json"
    data = json.loads(fetch(url))

    recent = data["filings"]["recent"]
    for i in range(len(recent["form"])):
        if recent["form"][i] == "10-K":
            return (
                recent["accessionNumber"][i],
                recent["primaryDocument"][i],
                recent["filingDate"][i],
            )
    return None


def extract_risk_factors(html: str) -> str | None:
    """Extract the Item 1A Risk Factors section from a 10-K HTML document."""
    start_pattern = re.compile(
        r"Item[\s\xa0]*1A[\.\s\xa0\u2014\u2013\-]*Risk\s*Factors", re.IGNORECASE
    )
    end_patterns = [
        re.compile(r"Item[\s\xa0]*1B", re.IGNORECASE),
        re.compile(r"Item[\s\xa0]*1C", re.IGNORECASE),
        re.compile(
            r"Item[\s\xa0]*2[\.\s\xa0\u2014\u2013\-]*(?:Properties|Unresolved)",
            re.IGNORECASE,
        ),
    ]

    starts = list(start_pattern.finditer(html))
    if not starts:
        return None

    # Use the last match to skip table-of-contents references
    section_start = starts[-1].start()

    section_end = len(html)
    for ep in end_patterns:
        for m in ep.finditer(html):
            if m.start() > section_start + 1000:
                section_end = min(section_end, m.start())
                break

    section_html = html[section_start:section_end]

    # Strip HTML to plain text
    text = re.sub(r"<[^>]+>", " ", section_html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&ldquo;|&rdquo;|&#8220;|&#8221;", '"', text)
    text = re.sub(r"&lsquo;|&rsquo;|&#8216;|&#8217;", "'", text)
    text = re.sub(r"&mdash;|&#8212;", " -- ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    text = text.strip()

    # Sanity check: risk factors should be substantial
    if len(text) < 500:
        return None

    return text


def download_filing(name: str, cik: str) -> Path | None:
    """Download and extract risk factors for one insurer."""
    filing_info = get_latest_10k(cik)
    if not filing_info:
        print(f"  {name}: no 10-K found")
        return None

    accession, primary_doc, filing_date = filing_info
    accession_clean = accession.replace("-", "")
    cik_num = cik.lstrip("0")

    url = f"{ARCHIVE_BASE}/{cik_num}/{accession_clean}/{primary_doc}"
    print(f"  {name}: downloading {filing_date} 10-K...")

    html = fetch(url)
    risk_text = extract_risk_factors(html)

    if not risk_text:
        print(f"  {name}: could not extract Risk Factors section")
        return None

    output_path = OUTPUT_DIR / f"{name.lower().replace(' ', '_')}_{filing_date}.txt"
    output_path.write_text(risk_text)

    # Also count paragraphs (useful for chunking later)
    paragraphs = [p.strip() for p in risk_text.split("\n\n") if len(p.strip()) > 50]

    print(
        f"  {name}: {len(risk_text):,} chars, {len(paragraphs)} paragraphs -> {output_path.name}"
    )
    return output_path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for name, cik in INSURERS.items():
        result = download_filing(name, cik)
        if result:
            downloaded.append(result)
        # SEC rate limit: 10 requests/second, be polite
        time.sleep(0.5)

    print(f"\ndownloaded {len(downloaded)}/{len(INSURERS)} filings to {OUTPUT_DIR}/")

    if downloaded:
        total_chars = sum(p.stat().st_size for p in downloaded)
        print(f"total text: {total_chars:,} chars across {len(downloaded)} files")


if __name__ == "__main__":
    main()
