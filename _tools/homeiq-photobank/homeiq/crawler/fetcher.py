"""
3-tier fetcher: httpx → Jina → Camoufox.

Each tier returns FetchResult. Auto-escalates on failure.
Camoufox is lazily imported (slow startup — only when needed).
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
import logging

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class FetchResult:
    url: str
    html: str
    status: int
    fetcher_tier: int          # 1 / 2 / 3
    final_url: str = ""
    elapsed_ms: int = 0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return bool(self.html) and self.status < 400 and not self._is_challenge()

    def _is_challenge(self) -> bool:
        snippet = self.html[:3000].lower()
        return (
            "just a moment" in snippet          # CF waiting room
            or "checking your browser" in snippet
            or "enable javascript" in snippet
            or (self.status == 403 and len(self.html) < 5000)
            or (self.status == 429)
        )


# ---------------------------------------------------------------------------
# User-Agent pool
# ---------------------------------------------------------------------------

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
]

def _random_headers() -> dict:
    # No Accept-Encoding — httpx handles decompression automatically.
    # Setting it manually breaks brotli decompression.
    return {
        "User-Agent": random.choice(_UA_POOL),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    }


# ---------------------------------------------------------------------------
# Tier 1 — httpx direct
# ---------------------------------------------------------------------------

async def _fetch_tier1(url: str, client: httpx.AsyncClient) -> FetchResult:
    t0 = time.monotonic()
    try:
        r = await client.get(url, headers=_random_headers(), timeout=30, follow_redirects=True)
        elapsed = int((time.monotonic() - t0) * 1000)
        return FetchResult(
            url=url,
            html=r.text,
            status=r.status_code,
            fetcher_tier=1,
            final_url=str(r.url),
            elapsed_ms=elapsed,
        )
    except httpx.TimeoutException:
        return FetchResult(url=url, html="", status=0, fetcher_tier=1, error="timeout")
    except Exception as e:
        return FetchResult(url=url, html="", status=0, fetcher_tier=1, error=str(e))


# ---------------------------------------------------------------------------
# Tier 2 — Jina reader  (r.jina.ai/{url})
# ---------------------------------------------------------------------------

async def _fetch_tier2(url: str, client: httpx.AsyncClient) -> FetchResult:
    jina_url = f"https://r.jina.ai/{url}"
    t0 = time.monotonic()
    try:
        r = await client.get(
            jina_url,
            headers={
                "User-Agent": random.choice(_UA_POOL),
                "Accept": "text/html,*/*",
                "X-Return-Format": "html",   # ask Jina to return raw HTML, not markdown
            },
            timeout=45,
            follow_redirects=True,
        )
        elapsed = int((time.monotonic() - t0) * 1000)
        return FetchResult(
            url=url,
            html=r.text,
            status=r.status_code,
            fetcher_tier=2,
            final_url=url,
            elapsed_ms=elapsed,
        )
    except httpx.TimeoutException:
        return FetchResult(url=url, html="", status=0, fetcher_tier=2, error="timeout")
    except Exception as e:
        return FetchResult(url=url, html="", status=0, fetcher_tier=2, error=str(e))


# ---------------------------------------------------------------------------
# Tier 3 — Camoufox headless browser
# ---------------------------------------------------------------------------

def _fetch_tier3_sync(url: str) -> FetchResult:
    """
    Spawn a child process running _camoufox_worker.py.
    Avoids Windows asyncio event loop conflicts with Playwright subprocess transport.
    """
    import subprocess
    import sys
    from pathlib import Path

    worker = Path(__file__).parent / "_camoufox_worker.py"
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, str(worker), url],
            capture_output=True,
            timeout=90,
        )
        elapsed = int((time.monotonic() - t0) * 1000)
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="replace").strip()
            return FetchResult(url=url, html="", status=0, fetcher_tier=3, error=err)
        html = proc.stdout.decode("utf-8", errors="replace")
        return FetchResult(url=url, html=html, status=200,
                           fetcher_tier=3, final_url=url, elapsed_ms=elapsed)
    except subprocess.TimeoutExpired:
        return FetchResult(url=url, html="", status=0, fetcher_tier=3, error="camoufox timeout")
    except Exception as e:
        return FetchResult(url=url, html="", status=0, fetcher_tier=3, error=str(e))


async def _fetch_tier3(url: str) -> FetchResult:
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_tier3_sync, url)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch(url: str, client: httpx.AsyncClient | None = None) -> FetchResult:
    """
    Fetch URL escalating through tiers until success.
    Pass an existing httpx.AsyncClient for connection reuse across many requests.
    """
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(http2=True)

    try:
        log.debug("Tier1 fetching: %s", url)
        result = await _fetch_tier1(url, client)
        if result.ok:
            return result

        log.info("Tier1 failed (status=%s), trying Tier2: %s", result.status, url)
        result = await _fetch_tier2(url, client)
        if result.ok:
            return result

        log.info("Tier2 failed (status=%s), trying Tier3: %s", result.status, url)
        result = await _fetch_tier3(url)
        log.info("Tier3 done: tier=%d status=%s elapsed=%dms url=%s",
                 result.fetcher_tier, result.status, result.elapsed_ms or 0, url)
        return result
    finally:
        if own_client:
            await client.aclose()


async def fetch_many(urls: list[str], client: httpx.AsyncClient | None = None) -> list[FetchResult]:
    """Fetch multiple URLs sharing one httpx client."""
    import asyncio
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(http2=True)
    try:
        return await asyncio.gather(*[fetch(u, client) for u in urls])
    finally:
        if own_client:
            await client.aclose()
