"""
Batch classifier — reads photos from unknown/ folders, classifies in parallel,
moves files to correct category folders, updates DB.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from pathlib import Path

from homeiq.classifier.vision_client import (
    VisionClient, ClassifyResult,
    CONFIDENCE_AUTO, CONFIDENCE_REVIEW,
)

log = logging.getLogger(__name__)

_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

# Pre-filter thresholds
_SOLID_COLOR_STD   = 18.0   # grayscale pixel std < this → solid color block
_MIN_LONG_EDGE     = 250    # px — below this → reject (too small; products are often small)
_HERO_MIN_AR       = 1.6    # aspect ratio — hero must be wider than tall
_PORTRAIT_MAX_AR   = 0.85   # portrait images are taller than wide


# ---------------------------------------------------------------------------
# Pre-filters (pure PIL/code — no API call)
# ---------------------------------------------------------------------------

def _get_image_info(image_path: Path):
    """Returns (width, height, pil_image) or None on failure."""
    try:
        from PIL import Image as PILImage
        img = PILImage.open(image_path)
        w, h = img.size
        return w, h, img
    except Exception:
        return None


def prefilter(image_path: Path) -> str | None:
    """
    Run deterministic pre-checks before sending to AI.
    Returns a forced category string if the image can be decided without AI,
    or None if AI classification is needed.
    """
    info = _get_image_info(image_path)
    if info is None:
        return "reject"

    w, h, img = info

    # 1. Too small → reject
    if max(w, h) < _MIN_LONG_EDGE:
        log.debug("prefilter: too small %dx%d → reject: %s", w, h, image_path.name)
        return "reject"

    # 2. Solid / near-solid color block → reject
    try:
        import statistics
        gray = img.convert("L")
        pixels = list(gray.getdata())
        if len(pixels) >= 100:
            std = statistics.stdev(pixels)
            if std < _SOLID_COLOR_STD:
                log.debug("prefilter: solid color std=%.1f → reject: %s", std, image_path.name)
                return "reject"
    except Exception:
        pass

    return None  # AI needed


def postfilter(result: ClassifyResult, image_path: Path) -> ClassifyResult:
    """
    Sanity-check the AI result with geometric rules.
    May downgrade confidence to force review queue.
    """
    info = _get_image_info(image_path)
    if info is None:
        return result

    w, h, _ = info
    ar = w / h if h > 0 else 1.0

    # hero must be landscape (wide)
    if result.category == "hero" and ar < _HERO_MIN_AR:
        log.debug("postfilter: hero but AR=%.2f (portrait) → confidence drop: %s",
                  ar, image_path.name)
        return ClassifyResult(
            result.category,
            min(result.confidence, 0.50),  # force into review
            result.runner_up,
            f"hero but portrait AR {ar:.2f}",
        )

    # portrait orientation + lifestyle/hero → likely a headshot
    if result.category in ("lifestyle", "hero") and ar < _PORTRAIT_MAX_AR:
        log.debug("postfilter: %s but portrait AR=%.2f → portrait: %s",
                  result.category, ar, image_path.name)
        return ClassifyResult(
            "portrait",
            min(result.confidence, 0.75),
            result.category,
            f"portrait orientation AR {ar:.2f}",
        )

    return result


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------

def find_unknown_photos(data_dir: Path, niche: str = "") -> list[Path]:
    """Find all image files in unknown/ subfolders under data_dir."""
    photos: list[Path] = []
    search_root = data_dir / niche if niche else data_dir
    for unknown_dir in search_root.rglob("unknown"):
        if not unknown_dir.is_dir():
            continue
        for f in unknown_dir.iterdir():
            if f.is_file() and f.suffix.lower() in _ALLOWED_EXT:
                photos.append(f)
    return sorted(photos)


def move_photo(photo_path: Path, category: str) -> Path:
    """Move photo from its current folder to sibling category/ folder."""
    new_dir = photo_path.parent.parent / category
    new_dir.mkdir(parents=True, exist_ok=True)
    new_path = new_dir / photo_path.name
    photo_path.rename(new_path)
    return new_path


def update_db(old_path: Path, new_path: Path, category: str, base_dir: Path) -> None:
    """Update section_tag and file_path in photos table."""
    from homeiq.db import get_session, Photo
    old_rel = str(old_path.relative_to(base_dir))
    new_rel = str(new_path.relative_to(base_dir))
    session = get_session()
    try:
        photo = session.query(Photo).filter_by(file_path=old_rel).first()
        if photo:
            photo.section_tag = category
            photo.file_path = new_rel
            session.commit()
        else:
            log.debug("No DB record for %s", old_rel)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Batch classification
# ---------------------------------------------------------------------------

async def classify_batch(
    photos: list[Path],
    client: VisionClient,
    max_concurrent: int = 5,
    dry_run: bool = False,
    base_dir: Path | None = None,
) -> dict[str, int]:
    """
    Classify all photos in parallel with semaphore-limited concurrency.

    Routing logic:
    - prefilter catches obvious rejects (solid color, too small)
    - AI classifies the rest
    - postfilter applies geometric sanity checks
    - confidence >= CONFIDENCE_AUTO  → auto-file in category/
    - confidence >= CONFIDENCE_REVIEW → auto-file but tagged needs_review
    - confidence <  CONFIDENCE_REVIEW → route to review/ folder
    - category == "unknown" → stays in unknown/

    Returns category → count mapping (review/ counted as "review").
    """
    if base_dir is None:
        from homeiq.crawler.downloader import BASE_DIR
        base_dir = BASE_DIR

    semaphore = asyncio.Semaphore(max_concurrent)
    counts: dict[str, int] = defaultdict(int)
    total = len(photos)

    async def process_one(i: int, photo: Path) -> None:
        async with semaphore:
            domain = photo.parent.parent.name

            # Pre-filter (no API call)
            forced = prefilter(photo)
            if forced is not None:
                result = ClassifyResult(forced, 1.0, forced, "prefilter")
            else:
                try:
                    result = await client.classify(photo)
                except Exception as e:
                    log.warning("classify error %s: %s", photo.name, e)
                    result = ClassifyResult("unknown", 0.0, "unknown", "error")

                # Post-filter geometric sanity check
                result = postfilter(result, photo)

            # Confidence-based routing
            if result.category == "unknown" or result.confidence == 0.0:
                dest_category = "unknown"
            elif result.confidence < CONFIDENCE_REVIEW:
                dest_category = "review"
            else:
                dest_category = result.category

            counts[dest_category] += 1

            # Console output
            conf_str = f"{result.confidence:.0%}"
            flag = "" if result.confidence >= CONFIDENCE_AUTO else " ?"
            print(f"[{i+1:4}/{total}] {dest_category:<14} {conf_str}{flag:<3} "
                  f"{domain}/{photo.name}  ({result.reason})")

            if not dry_run and dest_category not in ("unknown",):
                new_path = move_photo(photo, dest_category)
                update_db(photo, new_path, dest_category, base_dir)

    await asyncio.gather(*[process_one(i, p) for i, p in enumerate(photos)])
    return dict(counts)
