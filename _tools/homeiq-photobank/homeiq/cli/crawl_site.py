"""
Crawl an entire website and download all product/gallery/hero photos.

Usage:
    python -m homeiq.cli.crawl_site <url> --niche <niche> [--max-pages 100] [--section <section>]

Example:
    python -m homeiq.cli.crawl_site https://www.vivint.com/ --niche security
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from homeiq.logger import setup_logging
import logging
setup_logging()
log = logging.getLogger(__name__)

from homeiq.crawler.fetcher import fetch as async_fetch, _fetch_tier3_sync
from homeiq.crawler.extractors import extract_images
from homeiq.crawler.downloader import download_image, DATA_DIR, BASE_DIR
from homeiq.crawler.link_extractor import extract_links
from homeiq.crawler.section_detector import detect_section
from homeiq.db import init_db, get_session, Photo, Page, Site

# Tier fallback threshold: if Tier1 finds < this many images AND
# HTML is small (likely JS-rendered), re-fetch with Tier3
_MIN_IMAGES_TIER1 = 3
_MAX_HTML_FOR_FALLBACK = 80_000  # bytes — large HTML = SSR, small = SPA shell

from homeiq.config import cfg as _cfg

# Delay between page fetches (seconds)
_REQUEST_DELAY = _cfg.crawler.request_delay


def _save_to_db(session, dl_result, niche: str, section: str, page_id: int):
    photo = Photo(
        page_id=page_id,
        sha256_hash=dl_result.sha256,
        file_path=str(dl_result.file_path.relative_to(BASE_DIR)),
        original_url=dl_result.url,
        niche=niche,
        section_tag=section,
        width=dl_result.width,
        height=dl_result.height,
        file_size=dl_result.file_size,
        format=dl_result.fmt,
        source="scraped",
        approved=True,
        detected_at=datetime.utcnow(),
    )
    session.add(photo)


def _get_or_create_site(session, domain: str, niche: str, seed_url: str) -> int:
    site = session.query(Site).filter_by(domain=domain).first()
    if not site:
        site = Site(domain=domain, niche=niche, seed_url=seed_url, status="active")
        session.add(site)
        session.flush()
    elif site.niche != niche:
        log.warning("Site %s exists with niche='%s', requested niche='%s' — using existing",
                    domain, site.niche, niche)
    return site.id


def _get_or_create_page(session, site_id: int, url: str) -> int:
    page = session.query(Page).filter_by(url=url).first()
    if not page:
        page = Page(site_id=site_id, url=url, last_scraped=datetime.utcnow())
        session.add(page)
        session.flush()
    return page.id


def _load_existing_hashes(session) -> set[str]:
    return {row[0] for row in session.query(Photo.sha256_hash).all()}



async def _fetch_with_fallback(url: str) -> tuple:
    """
    Fetch url. If Tier1 result looks like an SPA shell (small HTML),
    also try Tier3 and return whichever gives more images.
    Returns (fetch_result, refs, tier_used_label)
    """
    result1 = await async_fetch(url)
    if not result1.ok:
        return result1, [], f"tier{result1.fetcher_tier}(failed)"

    refs1 = extract_images(result1.html, result1.final_url or url)

    # Decide if we should try Tier3
    html_size = len(result1.html.encode("utf-8", errors="replace"))
    needs_fallback = (
        len(refs1) < _MIN_IMAGES_TIER1
        and html_size < _MAX_HTML_FOR_FALLBACK
        and result1.fetcher_tier < 3
    )

    if not needs_fallback:
        return result1, refs1, f"tier{result1.fetcher_tier}"

    # Try Tier3
    try:
        import concurrent.futures
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            result3 = await loop.run_in_executor(pool, _fetch_tier3_sync, url)
        if result3 and result3.ok:
            refs3 = extract_images(result3.html, url)
            if len(refs3) > len(refs1):
                return result3, refs3, "tier3(fallback)"
    except Exception as e:
        log.warning("Tier3 fallback failed for %s: %s", url, e)

    return result1, refs1, f"tier{result1.fetcher_tier}"


def run(start_url: str, niche: str, default_section: str, max_pages: int):
    domain = urlparse(start_url).netloc
    log.info("Starting crawl: %s  niche=%s  max_pages=%d", start_url, niche, max_pages)
    print(f"\nCrawling: {start_url}  niche={niche}  max_pages={max_pages}\n")

    init_db()
    session = get_session()
    existing_hashes = _load_existing_hashes(session)
    site_id = _get_or_create_site(session, domain, niche, start_url)

    http_client = httpx.Client(http2=True, follow_redirects=True, timeout=20)

    visited: set[str] = set()
    queue: deque[str] = deque([start_url])
    visited.add(start_url)

    stats = {
        "pages": 0,
        "saved": 0,
        "duplicate": 0,
        "skipped": 0,
        "error": 0,
    }

    try:
        while queue and stats["pages"] < max_pages:
            page_url = queue.popleft()
            stats["pages"] += 1

            # Fetch page
            fetch_result, refs, tier_label = asyncio.run(
                _fetch_with_fallback(page_url)
            )

            if not fetch_result.ok:
                log.warning("Page failed [%d/%d]: %s", stats['pages'], max_pages, page_url)
                print(f"[{stats['pages']:3}/{max_pages}] FAIL  {page_url[:70]}")
                stats["error"] += 1
                time.sleep(_REQUEST_DELAY)
                continue

            # Extract new links and add to queue
            new_links = extract_links(fetch_result.html, page_url)
            added = 0
            for link in new_links:
                if link not in visited:
                    visited.add(link)
                    queue.append(link)
                    added += 1

            # Download images
            page_id = _get_or_create_page(session, site_id, page_url)
            page_saved = 0
            page_dup = 0

            for ref in refs:
                section = default_section or detect_section(ref)

                dl = download_image(
                    ref.url, niche, section,
                    existing_hashes=existing_hashes,
                    client=http_client,
                    pending=False,
                    domain=domain,
                    page_url=page_url,
                )

                if dl.status == "saved":
                    _save_to_db(session, dl, niche, section, page_id)
                    existing_hashes.add(dl.sha256)
                    stats["saved"] += 1
                    page_saved += 1
                elif dl.status == "duplicate":
                    stats["duplicate"] += 1
                    page_dup += 1
                elif dl.status == "skipped":
                    stats["skipped"] += 1
                elif dl.status == "error":
                    stats["error"] += 1
                    log.debug("Download error %s: %s", ref.url, dl.error)

            session.commit()

            print(
                f"[{stats['pages']:3}/{max_pages}] "
                f"{tier_label:<16} "
                f"{len(refs):2} imgs  "
                f"{page_saved:2} saved  "
                f"{page_dup:2} dup  "
                f"+{added} links  "
                f"{page_url[:60]}"
            )

            time.sleep(_REQUEST_DELAY)

    finally:
        http_client.close()
        session.rollback()
        session.close()

    print(f"\n{'='*60}")
    print(f"  Pages crawled: {stats['pages']}")
    print(f"  Photos saved:  {stats['saved']}")
    print(f"  Duplicates:    {stats['duplicate']}")
    print(f"  Skipped:       {stats['skipped']}")
    print(f"  Errors:        {stats['error']}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Crawl entire site and download product/gallery/hero photos"
    )
    parser.add_argument("url", help="Start URL (e.g. https://www.vivint.com/)")
    parser.add_argument("--niche", default="",
                        help="Niche name (e.g. security, bathroom). Auto-detected if omitted.")
    parser.add_argument("--section", default="",
                        help="Force section tag (skip auto-detect)")
    parser.add_argument("--max-pages", type=int, default=_cfg.crawler.max_pages,
                        help="Max pages to crawl (default: 100)")
    args = parser.parse_args()

    niche = args.niche
    if not niche:
        from homeiq.crawler.site_analyzer import analyze_url
        analysis = asyncio.run(analyze_url(args.url))
        niche = analysis.niche
        print(f"Niche auto-detected: {niche}")

    run(args.url, niche, args.section, args.max_pages)


if __name__ == "__main__":
    main()
