"""Export top-N largest hero photos from rebath.com to 16:9 WebP for landings.

Filters obvious junk (portrait, tiny, square logos masquerading as hero) but doesn't
do semantic detection — review the output and re-pick by hand if any photo isn't
actually a walk-in shower.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "data" / "bathroom" / "www.rebath.com" / "hero"
DEST = ROOT.parent.parent / "verticals" / "walk-in-shower" / "landings" / "_assets" / "hero"
DEST.mkdir(parents=True, exist_ok=True)

TARGET_W, TARGET_H = 1280, 720
N_FILES = 16
MIN_FILE_KB = 80
EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def is_landscape_like(path: Path) -> bool:
    """Accept square (1:1) and landscape (>=1:1). Skip portrait-dominant photos."""
    try:
        with Image.open(path) as im:
            w, h = im.size
            return w >= h * 0.95
    except Exception:
        return False


def crop_to_ratio(img: Image.Image, ratio: float) -> Image.Image:
    w, h = img.size
    src_ratio = w / h
    if src_ratio > ratio:
        new_w = int(h * ratio); offset = (w - new_w) // 2
        return img.crop((offset, 0, offset + new_w, h))
    new_h = int(w / ratio); offset = (h - new_h) // 2
    return img.crop((0, offset, w, offset + new_h))


candidates = [
    p for p in SRC_DIR.iterdir()
    if p.suffix.lower() in EXTS
    and p.stat().st_size >= MIN_FILE_KB * 1024
    and is_landscape_like(p)
]
candidates.sort(key=lambda p: -p.stat().st_size)
picks = candidates[:N_FILES]

print(f"Found {len(candidates)} eligible. Exporting top {len(picks)}.\n")

ratio = TARGET_W / TARGET_H
for idx, src in enumerate(picks, start=1):
    img = Image.open(src).convert("RGB")
    w0, h0 = img.size
    img = crop_to_ratio(img, ratio).resize((TARGET_W, TARGET_H), Image.LANCZOS)
    out = DEST / f"hero-{idx:02d}.webp"
    img.save(out, "WEBP", quality=88, method=6)
    print(f"{idx:>2}. {src.name:>32}  {w0}x{h0:<5} -> {out.name}  {out.stat().st_size//1024} KB")

# Keep the original primary file too for backwards compatibility with INDEX cards.
primary = DEST / "walk-in-shower-hero.webp"
if not primary.exists() and (DEST / "hero-01.webp").exists():
    primary.write_bytes((DEST / "hero-01.webp").read_bytes())

print(f"\nDestination: {DEST}")
