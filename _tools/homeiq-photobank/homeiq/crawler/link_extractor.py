"""
Extract, filter, normalize and prioritize internal links from a page's HTML.
"""
from __future__ import annotations

from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

_SKIP_EXTENSIONS = {".css", ".js", ".jpg", ".jpeg", ".png", ".webp",
                    ".svg", ".ico", ".pdf", ".zip", ".mp4", ".mp3"}

_SKIP_PATHS = [
    "/blog/", "/news/", "/careers/", "/jobs/", "/legal/", "/privacy/",
    "/terms/", "/faq/", "/sitemap/", "/login/", "/account/", "/cart/",
    "/checkout/", "/press/", "/investor/",
]

_PRIORITY_PATHS = [
    "/product", "/camera", "/gallery", "/solution", "/service",
    "/photo", "/image", "/install", "/smart-home", "/security",
]


def _normalize(url: str) -> str:
    """Remove fragment and query string, lowercase scheme+host."""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc.lower(), p.path, "", "", ""))


def _is_blocked(path: str) -> bool:
    path_lower = path.lower().rstrip("/") + "/"  # normalize trailing slash
    return any(path_lower.startswith(skip) for skip in _SKIP_PATHS)


def _is_static(path: str) -> bool:
    for ext in _SKIP_EXTENSIONS:
        if path.lower().endswith(ext):
            return True
    return False


def _priority(url: str) -> int:
    """Lower number = higher priority. 0=priority, 1=normal."""
    path = urlparse(url).path.lower()
    if any(kw in path for kw in _PRIORITY_PATHS):
        return 0
    return 1


def extract_links(html: str, base_url: str) -> list[str]:
    """
    Extract internal links from html relative to base_url.
    Returns deduplicated, normalized URLs sorted by priority
    (product/gallery pages first).
    """
    base = urlparse(base_url)
    base_domain = base.netloc.lower()

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return []

    seen: set[str] = set()
    results: list[str] = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue

        abs_url = urljoin(base_url, href)
        parsed = urlparse(abs_url)

        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc.lower() != base_domain:
            continue
        if _is_blocked(parsed.path):
            continue
        if _is_static(parsed.path):
            continue

        normalized = _normalize(abs_url)
        if normalized in seen:
            continue
        seen.add(normalized)
        results.append(normalized)

    results.sort(key=_priority)
    return results
