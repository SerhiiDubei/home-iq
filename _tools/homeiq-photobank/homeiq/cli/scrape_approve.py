"""
Scrape one URL, show each found image, ask Y/N approval before saving.

Usage:
    python -m homeiq.cli.scrape_approve <url> --niche <niche> [--section <section>]

Example:
    python -m homeiq.cli.scrape_approve https://www.homebuddy.com/walk-in-showers/ --niche shower

Controls:
    y  — approve & save to data/{niche}/{section}/
    n  — reject (skip)
    s  — skip rest, stop reviewing
    ?  — open image URL in browser
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path
from datetime import datetime

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from homeiq.crawler.fetcher import fetch as async_fetch
from homeiq.crawler.extractors import extract_images, ImageRef
from homeiq.crawler.downloader import download_image, PENDING_DIR
from homeiq.crawler.section_detector import detect_section
from homeiq.db import init_db, get_session, Photo, Page, Site

import asyncio



def _open_image(url: str):
    webbrowser.open(url)


def _show_info(i: int, total: int, ref: ImageRef, section: str):
    print(f"\n{'─'*60}")
    print(f"  [{i}/{total}] section guess: {section}")
    print(f"  alt  : {ref.alt_text or '(none)'}")
    if ref.width_hint:
        print(f"  size : {ref.width_hint}w")
    print(f"  url  : {ref.url[:90]}")
    print(f"{'─'*60}")
    print("  [y] approve  [n] reject  [?] open in browser  [s] stop")


def _load_existing_hashes(session) -> set[str]:
    return {row[0] for row in session.query(Photo.sha256_hash).all()}


def _save_to_db(session, result, niche: str, section: str,
                page_url: str, approved: bool):
    # find or create site
    from urllib.parse import urlparse
    domain = urlparse(page_url).netloc
    site = session.query(Site).filter_by(domain=domain).first()
    if not site:
        site = Site(domain=domain, niche=niche, seed_url=page_url,
                    status="active")
        session.add(site)
        session.flush()

    page = session.query(Page).filter_by(url=page_url).first()
    if not page:
        page = Page(site_id=site.id, url=page_url,
                    last_scraped=datetime.utcnow())
        session.add(page)
        session.flush()

    photo = Photo(
        page_id=page.id,
        sha256_hash=result.sha256,
        file_path=str(result.file_path.relative_to(
            Path(__file__).resolve().parents[2]
        )),
        original_url=result.url,
        niche=niche,
        section_tag=section,
        width=result.width,
        height=result.height,
        file_size=result.file_size,
        format=result.fmt,
        source="scraped",
        approved=approved,
        detected_at=datetime.utcnow(),
    )
    session.add(photo)
    session.commit()


def run(url: str, niche: str, default_section: str, auto: bool = False):
    print(f"\nFetching: {url}")
    result = asyncio.run(async_fetch(url))
    if not result.ok:
        print(f"Fetch failed: tier={result.fetcher_tier} status={result.status} "
              f"error={result.error}")
        sys.exit(1)

    print(f"  tier={result.fetcher_tier}  status={result.status}  "
          f"size={len(result.html):,}  elapsed={result.elapsed_ms}ms")

    refs = extract_images(result.html, result.final_url or url)
    if not refs:
        print("No images found on this page.")
        sys.exit(0)

    print(f"\nFound {len(refs)} image refs. Starting review...")

    init_db()
    session = get_session()
    existing = _load_existing_hashes(session)

    http_client = httpx.Client(http2=True, follow_redirects=True, timeout=20)

    stats = {"approved": 0, "rejected": 0, "duplicate": 0,
             "skipped": 0, "error": 0}

    try:
        for i, ref in enumerate(refs, 1):
            section = default_section or detect_section(ref)

            # Download to pending first
            dl = download_image(
                ref.url, niche, section,
                existing_hashes=existing,
                client=http_client,
                pending=True,
            )

            if dl.status == "duplicate":
                print(f"  [{i}/{len(refs)}] DUPLICATE — skip")
                stats["duplicate"] += 1
                continue
            if dl.status == "skipped":
                print(f"  [{i}/{len(refs)}] SKIPPED — {dl.error}")
                stats["skipped"] += 1
                continue
            if dl.status == "error":
                print(f"  [{i}/{len(refs)}] ERROR — {dl.error}")
                stats["error"] += 1
                continue

            if not auto:
                _show_info(i, len(refs), ref, section)

            def _save_approved():
                import shutil
                from homeiq.crawler.downloader import DATA_DIR as _DATA
                final_dir = _DATA / niche / section
                final_dir.mkdir(parents=True, exist_ok=True)
                final_path = final_dir / dl.file_path.name
                shutil.move(str(dl.file_path), str(final_path))
                result = type(dl)(
                    url=dl.url, status="saved", file_path=final_path,
                    sha256=dl.sha256, width=dl.width, height=dl.height,
                    file_size=dl.file_size, fmt=dl.fmt,
                )
                _save_to_db(session, result, niche, section, url, approved=True)
                existing.add(result.sha256)
                print(f"  [{i}/{len(refs)}] OK  {dl.width}x{dl.height}  "
                      f"{dl.file_size//1024}KB  {section}  {ref.url[:60]}")
                stats["approved"] += 1

            if auto:
                _save_approved()
                continue

            while True:
                choice = input("  > ").strip().lower()
                if choice == "y":
                    _save_approved()
                    break
                elif choice == "n":
                    dl.file_path.unlink(missing_ok=True)
                    stats["rejected"] += 1
                    break
                elif choice == "?":
                    _open_image(ref.url)
                elif choice == "s":
                    dl.file_path.unlink(missing_ok=True)
                    print("\nStopped by user.")
                    break
                else:
                    print("  y/n/?/s")
            else:
                continue
            if choice == "s":
                break

    finally:
        http_client.close()
        session.close()
        # Clean empty pending dirs
        import shutil as _shutil
        if PENDING_DIR.exists() and not list(PENDING_DIR.rglob("*.*")):
            _shutil.rmtree(str(PENDING_DIR), ignore_errors=True)

    print(f"\n{'='*60}")
    print(f"  Approved:   {stats['approved']}")
    print(f"  Rejected:   {stats['rejected']}")
    print(f"  Duplicates: {stats['duplicate']}")
    print(f"  Skipped:    {stats['skipped']}")
    print(f"  Errors:     {stats['error']}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape URL and approve images one by one"
    )
    parser.add_argument("url", help="Page URL to scrape")
    parser.add_argument("--niche", required=True,
                        help="Niche name (e.g. bathroom, hvac)")
    parser.add_argument("--section", default="",
                        help="Force section tag (skip auto-detect)")
    parser.add_argument("--auto", action="store_true",
                        help="Auto-approve all images without prompts")
    args = parser.parse_args()
    run(args.url, args.niche, args.section, auto=args.auto)


if __name__ == "__main__":
    main()
