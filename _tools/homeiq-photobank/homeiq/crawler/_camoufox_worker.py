"""
Standalone script called by fetcher Tier 3.
Uses sync Playwright Firefox (bundled) — Camoufox requires MSVC runtime not always present.
Falls back to Playwright Firefox which ships its own DLLs.
Prints HTML to stdout, exits 0 on success, 1 on failure.

Usage:
    python _camoufox_worker.py <url>
"""
import sys


def fetch_sync(url: str) -> str:
    from playwright.sync_api import sync_playwright  # type: ignore
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
                "Gecko/20100101 Firefox/125.0"
            )
        )
        page.goto(url, wait_until="networkidle", timeout=60_000)
        html = page.content()
        browser.close()
        return html


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: _camoufox_worker.py <url>", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    try:
        html = fetch_sync(url)
        sys.stdout.buffer.write(html.encode("utf-8"))
        sys.exit(0)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
