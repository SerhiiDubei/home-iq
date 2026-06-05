"""Export a before/after pair for v3-visual-proof slider.

Picks one strong "before" (mirrored 90s bathroom with tub) and one strong "after"
(clean marble walk-in shower) from data/bathroom/homeprousa.com/before_after/.
Crops both to 16:9 / 1280x720 WebP — same ratio so the slider clip-path matches.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "bathroom" / "homeprousa.com" / "before_after"
DEST = ROOT.parent.parent / "verticals" / "walk-in-shower" / "landings" / "_assets" / "before-after"
DEST.mkdir(parents=True, exist_ok=True)

# Hand-picked after visual review.
JOBS = [
    ("bfd34cc0a2db.webp", "before-01.webp"),   # mirrored old tub + clutter = classic "before"
    ("2fe67658b8c1.webp", "after-01.webp"),    # clean marble walk-in shower = "after"
]

TARGET_W, TARGET_H = 1280, 720  # 16:9


def crop_to_ratio(img: Image.Image, ratio: float) -> Image.Image:
    w, h = img.size
    src_ratio = w / h
    if src_ratio > ratio:
        new_w = int(h * ratio); offset = (w - new_w) // 2
        return img.crop((offset, 0, offset + new_w, h))
    new_h = int(w / ratio); offset = (h - new_h) // 2
    return img.crop((0, offset, w, offset + new_h))


ratio = TARGET_W / TARGET_H
for src_name, out_name in JOBS:
    src = SRC / src_name
    img = Image.open(src).convert("RGB")
    w0, h0 = img.size
    img = crop_to_ratio(img, ratio).resize((TARGET_W, TARGET_H), Image.LANCZOS)
    out = DEST / out_name
    img.save(out, "WEBP", quality=88, method=6)
    print(f"{src_name} {w0}x{h0} -> {out_name} {TARGET_W}x{TARGET_H}  {out.stat().st_size//1024} KB")

print(f"\nDestination: {DEST}")
