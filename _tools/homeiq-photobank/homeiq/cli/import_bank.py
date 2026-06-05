"""
Import existing photos from data/_import/ into the structured bank.

Usage:
    python -m homeiq.cli.import_bank [--dry-run]

Scans data/_import/ recursively, infers niche+section from:
  1. Parent folder names (e.g. _import/bathroom/ba/photo.jpg)
  2. Filename prefix   (e.g. bathroom_ba_together_001.jpg)
  3. Falls back to "unknown" if neither works

Moves files to data/{niche}/{section}/ and indexes in SQLite.
"""

import argparse
import hashlib
import shutil
import sys
from pathlib import Path
from datetime import datetime

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from homeiq.db import init_db, get_session, Photo

BASE_DIR = Path(__file__).resolve().parents[2]
IMPORT_DIR = BASE_DIR / "data" / "_import"
DATA_DIR = BASE_DIR / "data"
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

# Map common folder/filename tokens → canonical niche names
NICHE_ALIASES = {
    "bathroom": "bathroom",
    "bath": "bathroom",
    "bucket": "bucket",
    "gutter": "gutter",
    "flooring": "flooring",
    "floor": "floor",
    "hvac": "hvac",
    "security": "security",
    "shower": "shower",
    "siding": "siding",
    "home_warranty": "home_warranty",
    "home-warranty": "home_warranty",
    "homewarranty": "home_warranty",
    "kitchen": "kitchen",
    "plumbing": "plumbing",
    "roof": "roof",
    "solar": "solar",
    "walk_in_tubs": "walk_in_tubs",
    "walkintubs": "walk_in_tubs",
    "walk-in-tubs": "walk_in_tubs",
    "tubs": "walk_in_tubs",
}

SECTION_ALIASES = {
    "ba": "ba",
    "before_after": "ba",
    "before-after": "ba",
    "beforeafter": "ba",
    "together": "ba",   # bathroom_ba_together_... pattern
    "hero": "hero",
    "project": "project",
    "projects": "project",
    "finished": "finished",
    "finish": "finished",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_from_folder(path: Path) -> tuple[str | None, str | None]:
    """Walk parent parts of path looking for niche/section tokens."""
    parts = [p.lower().replace("-", "_") for p in path.parts]
    niche = None
    section = None
    for part in parts:
        if part in NICHE_ALIASES and niche is None:
            niche = NICHE_ALIASES[part]
        if part in SECTION_ALIASES and section is None:
            section = SECTION_ALIASES[part]
    return niche, section


def infer_from_filename(name: str) -> tuple[str | None, str | None]:
    """Parse tokens from filename like bathroom_ba_together_001.jpg"""
    stem = Path(name).stem.lower().replace("-", "_")
    tokens = stem.split("_")
    niche = None
    section = None
    for i, tok in enumerate(tokens):
        if tok in NICHE_ALIASES and niche is None:
            niche = NICHE_ALIASES[tok]
        if tok in SECTION_ALIASES and section is None:
            section = SECTION_ALIASES[tok]
        # "together" after "ba" confirms ba section
        if tok == "together" and i > 0 and tokens[i - 1] == "ba":
            section = "ba"
    return niche, section


def get_image_info(path: Path) -> tuple[int, int, int, str]:
    """Returns (width, height, file_size, format)."""
    file_size = path.stat().st_size
    try:
        with Image.open(path) as img:
            w, h = img.size
            fmt = img.format.lower() if img.format else path.suffix.lstrip(".")
    except Exception:
        w, h, fmt = 0, 0, path.suffix.lstrip(".")
    return w, h, file_size, fmt


def collect_files(import_dir: Path) -> list[Path]:
    files = []
    for p in import_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in ALLOWED_SUFFIXES:
            files.append(p)
    return files


def import_photo(path: Path, dry_run: bool, session) -> str:
    """Import one photo. Returns status: 'imported', 'duplicate', 'skipped'."""
    # Infer niche + section
    niche, section = infer_from_folder(path)
    fn, fs = infer_from_filename(path.name)
    niche = niche or fn or "unknown"
    section = section or fs or "unknown"

    # Check size
    file_size = path.stat().st_size
    if file_size < 500:
        return "skipped"

    # Hash
    sha = sha256_file(path)

    # Duplicate check
    existing = session.query(Photo).filter_by(sha256_hash=sha).first()
    if existing:
        return "duplicate"

    # Destination
    dest_dir = DATA_DIR / niche / section
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{sha[:12]}{path.suffix.lower()}"

    w, h, _, fmt = get_image_info(path)
    if w < 100 or h < 100:
        return "skipped"

    if not dry_run:
        shutil.copy2(path, dest)
        photo = Photo(
            sha256_hash=sha,
            file_path=str(dest.relative_to(BASE_DIR)),
            original_url=None,
            niche=niche,
            section_tag=section,
            width=w,
            height=h,
            file_size=file_size,
            format=fmt,
            source="imported",
            approved=True,   # existing bank = pre-approved
            detected_at=datetime.utcnow(),
        )
        session.add(photo)
        session.commit()

    return "imported"


def main():
    parser = argparse.ArgumentParser(description="Import existing photos into HomeIQ bank")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without moving files")
    args = parser.parse_args()

    if not IMPORT_DIR.exists():
        print(f"Import dir not found: {IMPORT_DIR}")
        sys.exit(1)

    files = collect_files(IMPORT_DIR)
    if not files:
        print(f"No images found in {IMPORT_DIR}")
        print("Put your photos there and run again.")
        sys.exit(0)

    print(f"Found {len(files)} images in {IMPORT_DIR}")
    if args.dry_run:
        print("DRY RUN — no files will be moved\n")

    init_db()
    session = get_session()

    stats = {"imported": 0, "duplicate": 0, "skipped": 0}
    niche_counts: dict[str, int] = {}

    for i, path in enumerate(files, 1):
        status = import_photo(path, args.dry_run, session)
        stats[status] += 1
        if status == "imported":
            _, section = infer_from_folder(path)
            fn, _ = infer_from_filename(path.name)
            niche = (infer_from_folder(path)[0] or fn or "unknown")
            niche_counts[niche] = niche_counts.get(niche, 0) + 1
        if i % 50 == 0:
            print(f"  {i}/{len(files)} processed...")

    session.close()

    print(f"\n{'DRY RUN ' if args.dry_run else ''}Results:")
    print(f"  Imported:   {stats['imported']}")
    print(f"  Duplicates: {stats['duplicate']}")
    print(f"  Skipped:    {stats['skipped']} (too small / tiny dimensions)")
    if niche_counts:
        print("\nBy niche:")
        for niche, count in sorted(niche_counts.items()):
            print(f"  {niche}: {count}")


if __name__ == "__main__":
    main()
