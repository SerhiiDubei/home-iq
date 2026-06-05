"""Capture mobile previews of every walk-in-shower landing.

Uses Playwright headless Chromium against the live Vercel URL, screenshots
at iPhone-SE viewport (375x667), then resizes to 300x533 WebP q=65 so
each thumb lands around 10-25 KB.

Output: verticals/walk-in-shower/landings/_assets/previews/preview-{slug}.webp
"""
from __future__ import annotations
import asyncio
from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
PREVIEW_DIR = ROOT.parent.parent / "verticals" / "walk-in-shower" / "landings" / "_assets" / "previews"
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://home-iq-dusky.vercel.app/verticals/walk-in-shower/landings"

# slug, url path (relative to BASE)
VARIANTS = [
    ("baseline",      "/baseline/index.html"),
    ("m1",            "/minor/m1-cta-benefit-copy/index.html"),
    ("m2",            "/minor/m2-headline-urgency/index.html"),
    ("m3",            "/minor/m3-trust-bar/index.html"),
    ("m4",            "/minor/m4-zip-first/index.html"),
    ("m5",            "/minor/m5-stars-compress/index.html"),
    ("midi-1",        "/midi/midi-1-trust-offer-lite/index.html"),
    ("midi-2",        "/midi/midi-2-urgent-hero/index.html"),
    ("midi-3",        "/midi/midi-3-social-first/index.html"),
    ("midi-4",        "/midi/midi-4-zip-trust/index.html"),
    ("midi-5",        "/midi/midi-5-benefit-stack/index.html"),
    ("styled-1",      "/styled/styled-1-editorial/index.html"),
    ("styled-2",      "/styled/styled-2-bold/index.html"),
    ("styled-3",      "/styled/styled-3-pastel/index.html"),
    ("styled-4",      "/styled/styled-4-dark/index.html"),
    ("styled-5",      "/styled/styled-5-retro/index.html"),
    ("v1",            "/v1-trust-offer/index.html"),
    ("v2",            "/v2-interactive-quiz/index.html"),
    ("v3",            "/v3-visual-proof/index.html"),
]

VIEWPORT = {"width": 375, "height": 667}
THUMB_W, THUMB_H = 300, 533  # 9:16
QUALITY = 65


async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            for slug, path in VARIANTS:
                ctx = await browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
                page = await ctx.new_page()
                url = BASE + path
                try:
                    await page.goto(url, wait_until="networkidle", timeout=25000)
                    await page.wait_for_timeout(700)  # give web fonts + bg images a beat
                    shot = await page.screenshot(full_page=False)
                except Exception as e:
                    print(f"  FAIL {slug:>10}  {type(e).__name__}: {e}")
                    await ctx.close()
                    continue
                await ctx.close()

                img = Image.open(BytesIO(shot)).convert("RGB")
                img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
                out = PREVIEW_DIR / f"preview-{slug}.webp"
                img.save(out, "WEBP", quality=QUALITY, method=6)
                kb = out.stat().st_size // 1024
                print(f"  {slug:>10}  {img.size!s:>11}  {kb:>3} KB")
        finally:
            await browser.close()


if __name__ == "__main__":
    print(f"Capturing {len(VARIANTS)} previews into {PREVIEW_DIR}")
    asyncio.run(capture())
    print("done.")
