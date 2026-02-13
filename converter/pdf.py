"""HTML to PDF conversion using weasyprint."""

import logging
import re

import weasyprint


def html_to_pdf(html_content: str, output_path: str, base_url: str = None) -> None:
    """Convert an HTML string to a PDF file using weasyprint.

    Args:
        html_content: The HTML content to convert.
        output_path: File path where the PDF will be saved.
        base_url: Base URL for resolving relative references in the HTML.
    """
    # SEC filing HTML produces many non-critical CSS warnings from weasyprint
    logging.getLogger("weasyprint").setLevel(logging.ERROR)
    logging.getLogger("fontTools").setLevel(logging.ERROR)

    # Remove excessive page breaks from SEC HTML to reduce blank pages
    # SEC filings often have CSS rules for print media that create unnecessary breaks
    html_content = _clean_page_breaks(html_content)

    html_doc = weasyprint.HTML(string=html_content, base_url=base_url)
    html_doc.write_pdf(output_path)


def _clean_page_breaks(html_content: str) -> str:
    """Remove or normalize excessive page-break CSS rules that cause blank pages.

    SEC HTML often includes CSS for print media with aggressive page breaks.
    This function removes some common patterns that cause unnecessary blank pages.
    """
    # Remove page-break-after: always from style attributes and CSS
    html_content = re.sub(
        r"page-break-after\s*:\s*always\s*;?", "", html_content, flags=re.IGNORECASE
    )

    # Remove page-break-before: always in most cases (keep some structure)
    html_content = re.sub(
        r"page-break-before\s*:\s*always\s*;?",
        "page-break-before: auto;",
        html_content,
        flags=re.IGNORECASE,
    )

    return html_content
