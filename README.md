# SEC EDGAR 10-K Report Fetcher

CLI tool that fetches the latest 10-K annual reports from the SEC EDGAR API and converts them to PDF format.

## Quick Start

### Prerequisites
- Docker


### Run with Pre-built Docker Image (Recommended)

The easiest way to use this tool is with the pre-built Docker image:

```bash
docker run -v ./output:/app/output ghcr.io/carnufex/quartr:main
```

### Build Docker Image Locally

If you prefer to build the image yourself:

```bash
docker build -t sec-10k-fetcher .
docker run -v ./output:/app/output sec-10k-fetcher
```


## Usage

```
python main.py [OPTIONS] [TICKERS...]
```

### Arguments

- `TICKERS` - One or more ticker symbols (default: AAPL META GOOGL AMZN NFLX GS)

### Options

- `--output-dir DIR` - Output directory for PDFs (default: `output/`)

### Examples

```bash
# Using pre-built image - default companies to output/ directory
docker run -v ./output:/app/output ghcr.io/carnufex/quartr:main

# Using pre-built image - specific tickers
docker run -v ./output:/app/output ghcr.io/carnufex/quartr:main AAPL META

# Using pre-built image - custom output directory
# Note: Volume mount path must match --output-dir argument
docker run -v ./reports:/app/reports ghcr.io/carnufex/quartr:main --output-dir reports AAPL

# Using locally built image - default companies
docker run -v ./output:/app/output sec-10k-fetcher

# Using locally built image - specific tickers
docker run -v ./output:/app/output sec-10k-fetcher AAPL META
```

## How It Works

1. Resolves ticker symbols to CIK numbers via SEC's company tickers endpoint
2. Fetches each company's filing history from the EDGAR submissions API
3. Finds the most recent 10-K filing in the submissions
4. Downloads the filing HTML document
5. Downloads and embeds referenced images as base64 data URLs
6. Measures table widths using JavaScript in Chromium
7. Calculates optimal scale factor to fit wide tables on the page
8. Converts the HTML to PDF using Playwright (Chromium engine)


## Project Structure

```
main.py              # CLI entry point and orchestrator
edgar/
  client.py          # SEC EDGAR HTTP client with rate limiting
  parser.py          # EDGAR response parsing and data extraction
converter/
  pdf.py             # HTML to PDF conversion using Playwright
requirements.txt     # Python dependencies (playwright, requests, beautifulsoup4)
Dockerfile           # Container with Python + Chromium
```