"""
Discover similar sites from a reference URL and crawl them all.

Usage:
    python -m homeiq.cli.discover_sites https://www.bathfitter.com/
    python -m homeiq.cli.discover_sites https://www.vivint.com/ --sites 10 --max-pages 30
    python -m homeiq.cli.discover_sites https://www.jameshardie.com/ --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from homeiq.logger import setup_logging
import logging
setup_logging()
log = logging.getLogger(__name__)

from homeiq.config import cfg  # used for exclude_domains, discovery_max_sites, discovery_skip_crawled
from homeiq.crawler.site_analyzer import analyze_url
from homeiq.crawler.search_client import SearchClient
from homeiq.db import init_db, get_session, Site


def build_site_list(reference_url: str, found_urls: list[str]) -> list[str]:
    """
    Prepend reference URL to found list, deduplicate by domain.
    Reference site is always first.
    """
    ref_domain = urlparse(reference_url).netloc.removeprefix("www.")
    seen: set[str] = {ref_domain}
    result: list[str] = [reference_url]

    for url in found_urls:
        domain = urlparse(url).netloc.removeprefix("www.")
        if domain and domain not in seen:
            seen.add(domain)
            result.append(url)

    return result


def format_summary(stats: list[dict]) -> str:
    total_photos = sum(s["saved"] for s in stats)
    total_sites = len(stats)
    return f"{total_sites} sites / {total_photos} photos total"


def _get_crawled_domains(session) -> set[str]:
    """Return set of domains already in the Site table."""
    rows = session.query(Site.domain).all()
    return {row[0] for row in rows}


def main():
    parser = argparse.ArgumentParser(
        description="Discover similar sites from a reference URL and crawl them all"
    )
    parser.add_argument("url", help="Reference site URL (e.g. https://www.bathfitter.com/)")
    parser.add_argument("--sites", type=int, default=5,
                        help="How many similar sites to find (default: 5)")
    parser.add_argument("--max-pages", type=int, default=20,
                        help="Pages to crawl per site (default: 20)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Find sites but do not crawl")
    args = parser.parse_args()

    reference_url = args.url
    if not reference_url.startswith("http"):
        reference_url = "https://" + reference_url

    # ── Step 1: Analyze reference site ──────────────────────────────────────
    print(f"\n[*] Analyzing reference site: {reference_url}")
    analysis = asyncio.run(analyze_url(reference_url))
    print(f"  Niche detected: {analysis.niche}")
    print(f"  Keywords: {', '.join(analysis.keywords)}")
    if analysis.title:
        print(f"  Title: {analysis.title}")

    # ── Step 2: Search for similar sites ────────────────────────────────────
    print(f"\n[>] Searching for similar sites via DuckDuckGo (up to {args.sites})...")

    init_db()
    session = get_session()
    try:
        crawled_domains = (
            _get_crawled_domains(session)
            if cfg.discovery_skip_crawled
            else set()
        )
    finally:
        session.close()

    exclude = set(cfg.exclude_domains)

    found_urls: list[str] = []
    client = SearchClient()
    found_urls = asyncio.run(
        client.find_sites(
            analysis.keywords,
            n=min(args.sites, cfg.discovery_max_sites),
            exclude_domains=exclude,
            crawled_domains=crawled_domains,
        )
    )

    # ── Step 3: Build final site list ───────────────────────────────────────
    all_sites = build_site_list(reference_url, found_urls)

    print(f"\n[list] Sites to crawl ({len(all_sites)}):")
    for i, url in enumerate(all_sites, 1):
        marker = " (reference)" if i == 1 else ""
        print(f"  {i}. {url}{marker}")

    if args.dry_run:
        print("\n[dry-run] Skipping crawl.")
        return

    # ── Step 4: Crawl each site ──────────────────────────────────────────────
    from homeiq.cli.crawl_site import run as crawl_run

    crawl_stats: list[dict] = []
    start_total = time.monotonic()

    for i, site_url in enumerate(all_sites, 1):
        print(f"\n{'-'*60}")
        print(f"[{i}/{len(all_sites)}] Crawling: {site_url}")
        print(f"{'-'*60}")

        try:
            crawl_run(
                start_url=site_url,
                niche=analysis.niche,
                default_section="",
                max_pages=args.max_pages,
            )
            crawl_stats.append({"url": site_url, "saved": 0, "pages": args.max_pages})
        except Exception as e:
            log.warning("Crawl failed for %s: %s", site_url, e)
            print(f"[WARN] Crawl failed for {site_url}: {e}")
            crawl_stats.append({"url": site_url, "saved": 0, "pages": 0})

    # ── Step 5: Final summary ────────────────────────────────────────────────
    elapsed = int(time.monotonic() - start_total)
    mins, secs = divmod(elapsed, 60)
    print(f"\n{'='*60}")
    print(f"  Discovery complete.")
    print(f"  Sites crawled: {len(all_sites)}")
    print(f"  Niche: {analysis.niche}")
    print(f"  Total time: {mins}m {secs}s")
    print(f"  Photos saved to: data/{analysis.niche}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
