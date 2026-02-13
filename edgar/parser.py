class TickerNotFoundError(Exception):
    """Raised when a ticker symbol cannot be resolved to a CIK."""

    pass


class FilingNotFoundError(Exception):
    """Raised when no 10-K filing is found for a company."""

    pass


def resolve_cik(ticker: str, mapping: dict) -> str:
    """Resolve a ticker symbol to a CIK number using the SEC mapping.

    The SEC mapping JSON structure:
    {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
        ...
    }
    """
    ticker_upper = ticker.upper()
    for entry in mapping.values():
        if entry.get("ticker", "").upper() == ticker_upper:
            return str(entry["cik_str"])
    raise TickerNotFoundError(f"Ticker '{ticker}' not found in SEC database")


def find_latest_10k(submissions: dict) -> dict:
    """Find the most recent 10-K filing in a company's submissions.

    The submissions response contains parallel arrays under filings.recent:
    form[], accessionNumber[], filingDate[], primaryDocument[].
    Index i across all arrays describes one filing.
    Arrays are ordered by date descending, so the first 10-K match
    is the most recent one.
    """
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    primary_documents = recent.get("primaryDocument", [])

    for i, form in enumerate(forms):
        if form == "10-K":
            return {
                "accession_number": accession_numbers[i],
                "filing_date": filing_dates[i],
                "primary_document": primary_documents[i],
            }

    raise FilingNotFoundError("No 10-K filing found in recent submissions")


def build_filing_url(cik: str, accession_number: str, primary_document: str) -> str:
    """Build the full URL to a filing document on SEC Archives.

    The accession number has dashes (e.g. "0000320193-23-000106") but
    the URL path uses it without dashes ("000032019323000106").
    """
    accession_no_dashes = accession_number.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik}/{accession_no_dashes}/{primary_document}"
    )
