#!/usr/bin/env python3
"""
Convert all JPG/PNG/GIF/JPEG images in landings/ to WebP.
Keeps originals as backup, updates HTML references.

WebP gives ~25-35% size reduction vs JPG with no visual quality loss
at quality=85. Universally supported by all modern browsers (95%+).
"""

import os
import re
from pathlib import Path
from PIL import Image

ROOT = Path("E:/Work Stuff/Home IQ/verticals/home-security/landings")
QUALITY = 85          # 85 is sweet spot for visual quality vs size
KEEP_ORIGINAL = True  # set False to delete originals after convert

# File extensions to convert
CONVERT_EXTS = {'.jpg', '.jpeg', '.png', '.gif'}

# Skip these (already webp/avif)
SKIP_EXTS = {'.webp', '.avif', '.svg'}


def convert_image(src_path: Path) -> Path | None:
    """Convert single image to .webp. Returns new path or None on error."""
    out_path = src_path.with_suffix('.webp')

    # Skip if already exists and is newer
    if out_path.exists() and out_path.stat().st_mtime >= src_path.stat().st_mtime:
        return out_path

    try:
        with Image.open(src_path) as im:
            # GIF: keep first frame only (we don't have animated needs)
            if src_path.suffix.lower() == '.gif':
                im = im.convert('RGBA' if 'transparency' in im.info else 'RGB')
            else:
                # PNG with alpha -> keep RGBA. JPG -> RGB
                if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                    im = im.convert('RGBA')
                else:
                    im = im.convert('RGB')

            im.save(out_path, 'WEBP', quality=QUALITY, method=6)
        return out_path
    except Exception as e:
        print(f'  ERROR converting {src_path}: {e}')
        return None


def update_html_refs(html_path: Path, replacements: dict):
    """Replace image filename references in HTML file."""
    content = html_path.read_text(encoding='utf-8')
    original = content

    for old_name, new_name in replacements.items():
        # Match: src="...old_name" or src="path/to/old_name" — only basename
        content = content.replace(f'/{old_name}"', f'/{new_name}"')
        content = content.replace(f'"{old_name}"', f'"{new_name}"')

    if content != original:
        html_path.write_text(content, encoding='utf-8')
        return True
    return False


def main():
    print(f"Scanning {ROOT}…\n")

    # Find all images that need conversion
    targets = []
    for ext in CONVERT_EXTS:
        targets.extend(ROOT.rglob(f'*{ext}'))

    print(f"Found {len(targets)} images to convert\n")

    # Convert and track size savings
    total_old = 0
    total_new = 0
    rename_map = {}  # filename -> new filename (for HTML rewriting)

    for src in targets:
        old_size = src.stat().st_size
        result = convert_image(src)
        if result and result.exists():
            new_size = result.stat().st_size
            total_old += old_size
            total_new += new_size
            saved_pct = 100 * (old_size - new_size) / old_size if old_size else 0
            print(f'  {src.name:50s} {old_size//1024:>5}KB -> {new_size//1024:>5}KB ({saved_pct:+.0f}%)')
            rename_map[src.name] = result.name

    # Update HTML references in all index.html
    print(f"\nUpdating HTML references…")
    html_files = list(ROOT.rglob('*.html'))
    for html_path in html_files:
        if update_html_refs(html_path, rename_map):
            print(f'  updated: {html_path.relative_to(ROOT)}')

    # Summary
    if total_old:
        saved_kb = (total_old - total_new) // 1024
        saved_pct = 100 * (total_old - total_new) / total_old
        print(f"\nOK Converted {len(rename_map)} files")
        print(f"  Total: {total_old//1024}KB -> {total_new//1024}KB (saved {saved_kb}KB, -{saved_pct:.1f}%)")

    # Cleanup originals?
    if not KEEP_ORIGINAL:
        for src in targets:
            if src.exists() and src.suffix.lower() in CONVERT_EXTS:
                src.unlink()
                print(f'  deleted original: {src.name}')


if __name__ == '__main__':
    main()
