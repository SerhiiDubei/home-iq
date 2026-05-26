#!/usr/bin/env python3
"""
Re-encode hero/critical images from sources at higher quality.

Strategy:
- Hero photos: quality=95, max width=2400px (Retina-ready)
- Resize down (LANCZOS) to reasonable max-width to balance size/quality
- Replace existing webp files in all landing folders
"""

import shutil
from pathlib import Path
from PIL import Image

LANDINGS = Path("E:/Work Stuff/Home IQ/verticals/home-security/landings")
SOURCES = Path("E:/Work Stuff/Home IQ/verticals/home-security/assets/incoming/Home Security")

# (source_path_relative_to_SOURCES, target_filename, max_width)
ASSETS = [
    # Hero photos — keep maximum quality
    ("wireless doorbell camera/smart-lock-vivint-doorbell-camera-front-door-blue-closeup.jpg",
        "hero-doorbell.webp", 2400),
    ("All/Lighthouse_lineup.jpg",
        "system-lineup.webp", 1800),
    ("Spotlight Pro/ring_spotlight_cam_pro_battery_white_hero_lifestyle_1500x1500_54eff973-6444-4502-b736-2d5ff66f73f1_2000x2000.jpg.jpg",
        "product-outdoor-cam.webp", 1800),
    # Other product cards
    ("wireless doorbell camera/doorbell-camera-pro-tech-install.jpg",
        "product-doorbell.webp", 1400),
    ("Door Windowsensor/hero_02.jpg",
        "product-sensor.webp", 1400),
    ("Motion sensor/Wide_motion-sensor-mounted-on-wall.webp",
        "product-motion.webp", 1400),
    ("Smart Lock/xiaomi-youdian-smart-zamok-cover.jpg",
        "product-lock.webp", 1400),
    ("Alarm control panel/hero-bg-2024.webp",
        "product-hub.webp", 1400),
    ("outdoor home security camera/contract_night_1880x.webp",
        "night-vision.webp", 1800),
    ("Smart Home/Photo-A.gif",
        "smart-home.webp", 1200),
    ("Smart Garage Door Opener/smart-garage-door-opener.jpg",
        "smart-garage.webp", 1200),
    ("Safery Alarm/smoke and CO detector.webp",
        "smoke-detector.webp", 1200),
]


def reencode(src: Path, max_width: int) -> bytes:
    """Re-encode an image to WebP bytes at quality=95."""
    with Image.open(src) as im:
        # Handle gif first frame
        if src.suffix.lower() == '.gif':
            im = im.convert('RGBA' if 'transparency' in im.info else 'RGB')
        elif im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
            im = im.convert('RGBA')
        else:
            im = im.convert('RGB')

        # Resize if wider than max_width
        if im.width > max_width:
            new_h = round(im.height * max_width / im.width)
            im = im.resize((max_width, new_h), Image.LANCZOS)

        # Save to memory then return bytes
        import io
        buf = io.BytesIO()
        im.save(buf, 'WEBP', quality=95, method=6)
        return buf.getvalue()


def main():
    print("Re-encoding from sources at quality=95...\n")

    total_old = 0
    total_new = 0

    for src_rel, target_name, max_w in ASSETS:
        src = SOURCES / src_rel
        if not src.exists():
            print(f"  SKIP missing: {src_rel}")
            continue

        try:
            new_bytes = reencode(src, max_w)
        except Exception as e:
            print(f"  ERROR {target_name}: {e}")
            continue

        # Find every copy of this target across landing folders and replace
        count = 0
        for existing in LANDINGS.rglob(target_name):
            old_size = existing.stat().st_size if existing.exists() else 0
            existing.write_bytes(new_bytes)
            new_size = existing.stat().st_size
            total_old += old_size
            total_new += new_size
            count += 1

        print(f"  {target_name:30s} src={src.stat().st_size//1024}KB  ->  {len(new_bytes)//1024}KB  (x{count} folders)")

    if total_old:
        saved_pct = 100 * (total_new - total_old) / total_old
        print(f"\nTotal across all folders: {total_old//1024}KB -> {total_new//1024}KB ({saved_pct:+.1f}%)")


if __name__ == '__main__':
    main()
