"""HTML to PDF conversion using Playwright (Chromium)."""

import base64
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Letter paper usable width in CSS pixels (8.5in * 96dpi - margins)
_LETTER_WIDTH_PX = 816 - 96  # 8.5in minus ~0.5in margins each side = ~720px


def html_to_pdf(html_content: str, output_path: str, base_url: str = None) -> None:
    """Convert an HTML string to a PDF file using Playwright (Chromium).

    Uses a real browser engine for accurate table rendering. Automatically
    scales content down if tables are wider than the page.

    Args:
        html_content: The HTML content to convert.
        output_path: File path where the PDF will be saved.
        base_url: Base URL for resolving relative references in the HTML.
    """
    if base_url:
        html_content = _make_images_absolute(html_content, base_url)

    # Inject CSS to ensure page breaks work in Chromium print-to-PDF
    html_content = _inject_print_css(html_content)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.set_content(html_content, wait_until="networkidle")

        scale = _calculate_scale(page)

        page.pdf(
            path=output_path,
            format="Letter",
            scale=scale,
            print_background=True,
            margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"},
        )

        browser.close()


def _calculate_scale(page) -> float:
    """Measure content width and calculate the scale needed to fit the page.

    Uses JavaScript to find the widest element on the page, then returns
    a scale factor that makes everything fit within the page width.
    Only scales down (never up).
    """
    max_width = page.evaluate("""() => {
        const body = document.body;
        if (!body) return 0;

        let maxW = body.scrollWidth;

        // Check all tables specifically since they're the usual culprits
        const tables = document.querySelectorAll('table');
        for (const table of tables) {
            maxW = Math.max(maxW, table.scrollWidth);
        }

        return maxW;
    }""")

    if max_width <= 0:
        return 1.0

    # Letter width minus margins: 8.5in = 816px at 96dpi, minus 1cm margins each side
    usable_width = _LETTER_WIDTH_PX
    scale = usable_width / max_width

    # Clamp: never scale up, and Playwright accepts 0.1 - 2.0
    return max(0.1, min(1.0, scale))


def _make_images_absolute(html_content: str, base_url: str) -> str:
    """Download images and embed them as base64 data URLs.

    SEC filings often reference images with relative paths. This function
    downloads them and embeds them directly in the HTML as data URLs,
    ensuring they load properly in Playwright.

    Args:
        html_content: The HTML content to process.
        base_url: The base URL to resolve relative paths against.

    Returns:
        HTML content with base64-encoded inline images.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Create a session with SEC-compatible User-Agent
    session = requests.Session()
    session.headers.update({
        "User-Agent": "QuartrAssignment@default.com",
        "Accept-Encoding": "gzip, deflate",
    })

    for img in soup.find_all("img"):
        if not img.has_attr("src"):
            continue

        img_url = urljoin(base_url, img["src"])

        # Skip if already a data URL
        if img_url.startswith("data:"):
            continue

        try:
            # Download the image
            response = session.get(img_url, timeout=10)
            response.raise_for_status()

            # Detect content type
            content_type = response.headers.get("Content-Type", "image/jpeg")

            # Convert to base64 data URL
            img_data = base64.b64encode(response.content).decode("utf-8")
            data_url = f"data:{content_type};base64,{img_data}"

            img["src"] = data_url

        except (requests.RequestException, ValueError, KeyError):
            # If image download fails, leave the original URL
            # (will show as broken image in PDF)
            pass

    return str(soup)


def _inject_print_css(html_content: str) -> str:
    """Inject CSS to ensure page breaks work correctly in Chromium.

    SEC filings use inline styles like <hr style="page-break-after:always">
    which Chromium doesn't always respect in print-to-PDF mode. This function
    injects CSS rules that explicitly handle page breaks.

    Args:
        html_content: The HTML content to process.

    Returns:
        HTML content with injected print CSS.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Create print CSS
    style_tag = soup.new_tag("style")
    style_tag.string = """
        @media print {
            /* Force page breaks on HR elements with page-break-after */
            hr[style*="page-break-after"] {
                page-break-after: always !important;
                break-after: always !important;
                display: block !important;
                height: 0 !important;
                border: none !important;
                margin: 0 !important;
                padding: 0 !important;
            }

            /* Force page breaks on any element with page-break-before */
            [style*="page-break-before"] {
                page-break-before: always !important;
                break-before: always !important;
            }

            /* Prevent page breaks inside table rows */
            tr {
                page-break-inside: avoid !important;
                break-inside: avoid !important;
            }
        }
    """

    # Insert at the beginning of <head> or create <head> if missing
    head = soup.find("head")
    if head:
        head.insert(0, style_tag)
    else:
        html_tag = soup.find("html")
        if html_tag:
            new_head = soup.new_tag("head")
            html_tag.insert(0, new_head)
            new_head.append(style_tag)
        else:
            # No HTML structure, just prepend
            soup.insert(0, style_tag)

    return str(soup)
