"""HTTP client for the SEC EDGAR API with rate limiting and error handling."""

import time

import requests


class EdgarClientError(Exception):
    """Raised when an SEC EDGAR API request fails."""


class EdgarClient:
    """HTTP client for the SEC EDGAR API with rate limiting."""

    TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
    MIN_REQUEST_INTERVAL = 0.1  # 10 requests/second max

    def __init__(self, user_agent: str):
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept-Encoding": "gzip, deflate",
            }
        )
        self._last_request_time = 0.0

    def _rate_limit(self):
        """Enforce SEC's 10 requests/second rate limit."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str) -> requests.Response:
        """Make a rate-limited GET request."""
        self._rate_limit()
        try:
            response = self._session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "unknown"
            raise EdgarClientError(f"HTTP {status} for {url}") from e
        except requests.exceptions.ConnectionError as e:
            raise EdgarClientError(f"Connection failed for {url}") from e
        except requests.exceptions.Timeout as e:
            raise EdgarClientError(f"Request timed out for {url}") from e

    def fetch_ticker_to_cik_mapping(self) -> dict:
        """Fetch the global ticker-to-CIK mapping from SEC."""
        response = self._get(self.TICKERS_URL)
        return response.json()

    def fetch_company_submissions(self, cik: str) -> dict:
        """Fetch filing submissions for a company by CIK number."""
        padded_cik = cik.zfill(10)
        url = self.SUBMISSIONS_URL.format(cik=padded_cik)
        response = self._get(url)
        return response.json()

    def fetch_filing_document(self, url: str) -> str:
        """Fetch the HTML content of a filing document."""
        response = self._get(url)
        return response.text
