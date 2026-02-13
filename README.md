# SEC EDGAR 10-K Report Fetcher

CLI tool that fetches the latest 10-K annual reports from the SEC EDGAR API and converts them to PDF format.

## Quick Start

### Prerequisites

- **Docker** - Recommended for all platforms
- Python 3.10+ (for local development)
- On Linux/macOS: system libraries for weasyprint (Pango, Cairo, GDK-Pixbuf)
- On Windows: Docker is strongly recommended as weasyprint requires GTK libraries that are complex to install

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

### Run with Python

**Note:** This approach has not been verified, but should work on Linux/macOS with proper system libraries installed. Windows users should use Docker instead due to weasyprint's GTK dependencies.

```bash
pip install -r requirements.txt
python main.py
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

# Using Python directly - default companies
python main.py

# Using Python directly - specific companies
python main.py AAPL META

# Using Python directly - custom output directory
python main.py --output-dir reports AAPL META
```

## How It Works

1. Resolves ticker symbols to CIK numbers via SEC's company tickers endpoint
2. Fetches each company's filing history from the EDGAR submissions API
3. Finds the most recent 10-K filing in the submissions
4. Downloads the filing HTML document
5. Converts the HTML to PDF using weasyprint

## Project Structure

```
main.py              # CLI entry point and orchestrator
edgar/
  client.py          # SEC EDGAR HTTP client with rate limiting
  parser.py          # EDGAR response parsing and data extraction
converter/
  pdf.py             # HTML to PDF conversion
requirements.txt     # Python dependencies
Dockerfile           # Container build instructions
```