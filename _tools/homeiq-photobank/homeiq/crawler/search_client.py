"""
DuckDuckGo HTML scraper — finds similar sites by keyword.

No API key required. Scrapes https://html.duckduckgo.com/html/?q=<query>
and extracts result URLs via BeautifulSoup.

Usage:
    from homeiq.crawler.search_client import SearchClient
    client = SearchClient()
    urls = await client.find_sites(["bathroom remodeling", "tub replacement"], n=5)
"""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Optional
from urllib.parse import urlparse, unquote

import httpx
from bs4 import BeautifulSoup

from homeiq.crawler.site_analyzer import is_contractor_site

log = logging.getLogger(__name__)

_DDG_URL = "https://html.duckduckgo.com/html/"

_QUERY_TEMPLATES = [
    "{kw} company free quote residential USA",
    "{kw} installation contractor get estimate",
    "{kw} home services licensed insured",
]

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


def build_queries(keywords: list[str]) -> list[str]:
    """Build 3 search query strings from keywords list using first keyword as primary."""
    primary = keywords[0] if keywords else "home services"
    return [t.format(kw=primary) for t in _QUERY_TEMPLATES]


def filter_urls(
    urls: list[str],
    exclude_domains: set[str],
    crawled_domains: set[str],
) -> list[str]:
    """Remove excluded/already-crawled domains, deduplicate by domain. Returns root URLs."""
    seen_domains: set[str] = set()
    result: list[str] = []

    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            continue
        domain = parsed.netloc.removeprefix("www.")
        if not domain:
            continue
        if any(exc in domain for exc in exclude_domains):
            continue
        if domain in crawled_domains:
            continue
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        result.append(f"{parsed.scheme}://{parsed.netloc}/")

    return result


def _parse_ddg_results(html: str) -> list[str]:
    """Extract result URLs from DuckDuckGo HTML page."""
    soup = BeautifulSoup(html, "lxml")
    urls: list[str] = []

    # DDG HTML results: <a class="result__a" href="...">
    for a in soup.select("a.result__a"):
        href = a.get("href", "")
        if not href:
            continue
        # DDG sometimes wraps URLs in /l/?uddg=<encoded_url>
        if href.startswith("/l/") and "uddg=" in href:
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(href).query)
            real = qs.get("uddg", [""])[0]
            if real:
                href = unquote(real)
        if href.startswith("http"):
            urls.append(href)

    return urls


class SearchClient:
    def __init__(self, api_key: str = ""):
        # api_key kept for interface compatibility but not used (DDG needs no key)
        pass

    async def find_sites(
        self,
        keywords: list[str],
        n: int = 5,
        exclude_domains: Optional[set[str]] = None,
        crawled_domains: Optional[set[str]] = None,
    ) -> list[str]:
        """Search DuckDuckGo for sites matching keywords. Returns up to n unique root URLs."""
        exclude_domains = exclude_domains or set()
        crawled_domains = crawled_domains or set()
        queries = build_queries(keywords)
        all_urls: list[str] = []

        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            headers={
                "User-Agent": random.choice(_UA_POOL),
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            for query in queries:
                urls = await self._search_one(client, query)
                all_urls.extend(urls)
                # Polite delay between requests
                await asyncio.sleep(2.0)

            filtered = filter_urls(all_urls, exclude_domains, crawled_domains)
            validated = await self._validate_sites(client, filtered, n)

        return validated

    async def _validate_sites(
        self, client: httpx.AsyncClient, candidates: list[str], n: int
    ) -> list[str]:
        """
        Fetch each candidate homepage and check is_contractor_site().
        Passes if validation succeeds OR if fetch fails (include-on-error).
        Stops once n valid sites are found.
        """
        result: list[str] = []
        for url in candidates:
            if len(result) >= n:
                break
            try:
                r = await client.get(
                    url,
                    headers={"User-Agent": random.choice(_UA_POOL)},
                    timeout=10,
                )
                html = r.text if r.status_code == 200 else ""
            except Exception:
                html = ""

            if not html:
                # Cannot fetch → include by default (don't discard)
                log.debug("Validator: fetch failed for %s, including by default", url)
                result.append(url)
                continue

            if is_contractor_site(html):
                log.debug("Validator: PASS contractor site %s", url)
                result.append(url)
            else:
                log.info("Validator: SKIP non-contractor site %s", url)

        return result

    async def _search_one(self, client: httpx.AsyncClient, query: str) -> list[str]:
        """Single DuckDuckGo HTML query → list of result URLs."""
        try:
            r = await client.post(
                _DDG_URL,
                data={"q": query, "b": "", "kl": "us-en"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if r.status_code != 200:
                log.warning("DDG returned %d for query: %s", r.status_code, query)
                return []
            urls = _parse_ddg_results(r.text)
            log.debug("DDG query '%s' -> %d URLs", query, len(urls))
            return urls
        except Exception as e:
            log.warning("DDG search failed for '%s': %s", query, e)
            return []
