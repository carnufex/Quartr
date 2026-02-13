"""CLI tool for fetching and converting SEC EDGAR 10-K reports to PDF."""

import argparse
import os
import sys

from edgar.client import EdgarClient, EdgarClientError
from edgar.parser import (
    FilingNotFoundError,
    TickerNotFoundError,
    build_filing_url,
    find_latest_10k,
    resolve_cik,
)
from converter.pdf import html_to_pdf


DEFAULT_TICKERS = ["AAPL", "META", "GOOGL", "AMZN", "NFLX", "GS"]
DEFAULT_OUTPUT_DIR = "output"
USER_AGENT = "QuartrAssignment@default.com"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch latest 10-K filings from SEC EDGAR and convert to PDF."
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        default=DEFAULT_TICKERS,
        help="Ticker symbols (default: AAPL META GOOGL AMZN NFLX GS)",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save PDFs (default: output/)",
    )
    return parser.parse_args()


def main():
    """Main entry point for the CLI application."""
    args = parse_args()
    tickers = [t.upper() for t in args.tickers]
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    client = EdgarClient(user_agent=USER_AGENT)

    print("Fetching ticker-to-CIK mapping...")
    ticker_mapping = client.fetch_ticker_to_cik_mapping()

    results = []

    for ticker in tickers:
        try:
            print(f"\nProcessing {ticker}...")

            cik = resolve_cik(ticker, ticker_mapping)
            print(f"  CIK: {cik}")

            submissions = client.fetch_company_submissions(cik)

            filing = find_latest_10k(submissions)
            print(f"  Latest 10-K filed: {filing['filing_date']}")

            url = build_filing_url(
                cik, filing["accession_number"], filing["primary_document"]
            )
            print("  Fetching filing document...")
            html_content = client.fetch_filing_document(url)

            filename = f"{ticker}_10K_{filing['filing_date']}.pdf"
            output_path = os.path.join(output_dir, filename)
            print("  Converting to PDF...")
            html_to_pdf(html_content, output_path, base_url=url)
            print(f"  Saved: {output_path}")

            results.append((ticker, "success", output_path))

        except (TickerNotFoundError, FilingNotFoundError, EdgarClientError) as e:
            print(f"  ERROR: {e}")
            results.append((ticker, "failed", str(e)))

    print("\n" + "=" * 50)
    print("Summary:")
    for ticker, status, detail in results:
        icon = "OK" if status == "success" else "FAIL"
        print(f"  [{icon}] {ticker}: {detail}")

    failed = sum(1 for _, status, _ in results if status == "failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
