"""
Classify photos from unknown/ folders using AI Vision.

Usage:
    python -m homeiq.cli.classify_photos [--niche security] [--dry-run] [--limit 100]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from homeiq.logger import setup_logging
import logging
setup_logging()
log = logging.getLogger(__name__)

from homeiq.config import cfg
from homeiq.classifier.vision_client import VisionClient
from homeiq.classifier.batch_classifier import find_unknown_photos, classify_batch
from homeiq.crawler.downloader import BASE_DIR, DATA_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Classify unknown photos using AI Vision (Gemini via OpenRouter)"
    )
    parser.add_argument("--niche", default="",
                        help="Process only this niche (default: all niches)")
    parser.add_argument("--folder", default="",
                        help="Specific folder path instead of unknown/ subfolders")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without moving files")
    parser.add_argument("--limit", type=int, default=0,
                        help="Process only first N photos")
    parser.add_argument("--model", default="",
                        help="Override model from config.yaml")
    args = parser.parse_args()

    # API key
    api_key = cfg.classifier.openrouter_api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("ERROR: OpenRouter API key not set.")
        print("  Option 1: config.yaml  ->  classifier.openrouter_api_key: \"your-key\"")
        print("  Option 2: set env var  ->  OPENROUTER_API_KEY=your-key")
        sys.exit(1)

    # Find photos
    if args.folder:
        folder = Path(args.folder)
        if not folder.is_absolute():
            folder = BASE_DIR / folder
        photos = [f for f in folder.iterdir()
                  if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    else:
        photos = find_unknown_photos(DATA_DIR, args.niche)

    if args.limit:
        photos = photos[:args.limit]

    if not photos:
        print("No photos found to classify.")
        if not args.niche:
            print("Tip: all unknown/ folders are empty. Run discover.bat first.")
        return

    # Setup
    model = args.model or cfg.classifier.model
    fallback = cfg.classifier.fallback_model

    print(f"\nClassifying {len(photos)} photos")
    print(f"Model:    {model}")
    print(f"Fallback: {fallback}")
    if args.niche:
        print(f"Niche:    {args.niche}")
    if args.dry_run:
        print("DRY RUN  - no files will be moved\n")
    else:
        print()

    client = VisionClient(api_key=api_key, model=model, fallback_model=fallback)

    # Run
    t0 = time.monotonic()
    counts = asyncio.run(classify_batch(
        photos, client,
        max_concurrent=cfg.classifier.max_concurrent,
        dry_run=args.dry_run,
        base_dir=BASE_DIR,
    ))
    elapsed = int(time.monotonic() - t0)
    mins, secs = divmod(elapsed, 60)

    # Report
    total = sum(counts.values())
    est_cost = total * cfg.classifier.cost_per_image_usd

    review_count = counts.get("review", 0)
    auto_count = total - review_count - counts.get("unknown", 0)

    print(f"\n{'='*60}")
    print(f"  Classified:      {total} photos")
    print(f"  Auto-filed:      {auto_count} ({int(auto_count/total*100) if total else 0}%)")
    print(f"  Review queue:    {review_count} ({int(review_count/total*100) if total else 0}%)")
    print(f"  Time:            {mins}m {secs}s")
    print(f"  Est. cost:       ${est_cost:.4f}")
    print()
    # Show review/ first if non-empty, then categories by count
    order = sorted(counts.items(), key=lambda x: (x[0] != "review", -x[1]))
    for cat, n in order:
        pct = int(n / total * 100) if total else 0
        bar = "#" * (pct // 5)
        marker = " <-- check these" if cat == "review" else ""
        print(f"  {cat:<16} {n:4} ({pct:2}%) {bar}{marker}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
