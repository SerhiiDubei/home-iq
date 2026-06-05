"""
Download a single image URL → validate → sha256 dedup → save to disk.

Returns DownloadResult with status: saved / duplicate / skipped / error
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image as PILImage

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
PENDING_DIR = DATA_DIR / "_pending"

from homeiq.config import cfg
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXT  = {".jpg", ".jpeg", ".png", ".webp"}
MIN_BYTES = cfg.crawler.min_file_bytes
MAX_BYTES = cfg.crawler.max_file_bytes
MIN_DIM   = cfg.crawler.min_dimension_px


@dataclass
class DownloadResult:
    url: str
    status: str          # saved / duplicate / skipped / error
    file_path: Optional[Path] = None
    sha256: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    fmt: Optional[str] = None
    error: Optional[str] = None


def _ext_from_url(url: str) -> str:
    from urllib.parse import urlparse
    path = urlparse(url).path.lower()
    for ext in ALLOWED_EXT:
        if path.endswith(ext):
            return ext
    return ".jpg"


def _ext_from_content_type(ct: str) -> str:
    ct = ct.split(";")[0].strip().lower()
    return {
        "image/jpeg": ".jpg",
        "image/png":  ".png",
        "image/webp": ".webp",
    }.get(ct, ".jpg")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_RETRY_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


def download_image(
    url: str,
    niche: str,
    section: str,
    existing_hashes: set[str],
    client: Optional[httpx.Client] = None,
    pending: bool = False,
    domain: str = "",
    page_url: str = "",
) -> DownloadResult:
    """
    Download image synchronously.
    - existing_hashes: set of sha256 already in DB — skip if hit
    - page_url: the page that referenced this image (used as Referer)
    - pending=True: save to data/_pending/{niche}/{section}/
    - pending=False, domain="": save to data/{niche}/{section}/
    - pending=False, domain="vivint.com": save to data/{niche}/vivint.com/{section}/
    """
    own = client is None
    if own:
        client = httpx.Client(http2=True, follow_redirects=True, timeout=20)
    try:
        return _do_download(url, niche, section, existing_hashes, client, pending, domain, page_url)
    finally:
        if own:
            client.close()


def _do_download(url, niche, section, existing_hashes, client, pending, domain="", page_url="") -> DownloadResult:
    import random
    referer = page_url or url

    # 1. Fetch — with retry on 403/429 using different User-Agents
    resp = None
    last_error: Optional[str] = None
    for ua in _RETRY_UA:
        try:
            r = client.get(
                url,
                headers={
                    "User-Agent": ua,
                    "Referer": referer,
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Sec-Fetch-Dest": "image",
                    "Sec-Fetch-Mode": "no-cors",
                    "Sec-Fetch-Site": "same-origin",
                },
            )
            if r.status_code in (403, 429):
                last_error = f"HTTP {r.status_code}"
                continue  # retry with next UA
            r.raise_for_status()
            resp = r
            break
        except httpx.HTTPStatusError as e:
            last_error = str(e)
            continue
        except Exception as e:
            return DownloadResult(url=url, status="error", error=str(e))

    if resp is None:
        return DownloadResult(url=url, status="error", error=last_error or "all UA attempts failed")

    data = resp.content

    # 2. Size check
    if len(data) < MIN_BYTES:
        return DownloadResult(url=url, status="skipped", error="too small")
    if len(data) > MAX_BYTES:
        return DownloadResult(url=url, status="skipped", error="too large")

    # 3. Content-type / extension
    ct = resp.headers.get("content-type", "")
    if ct and not any(m in ct for m in ["jpeg", "png", "webp", "image"]):
        return DownloadResult(url=url, status="skipped", error=f"bad content-type: {ct}")
    ext = _ext_from_content_type(ct) if ct else _ext_from_url(url)

    # 4. Hash dedup
    sha = sha256_bytes(data)
    if sha in existing_hashes:
        return DownloadResult(url=url, status="duplicate", sha256=sha)

    # 5. Image validation
    try:
        from io import BytesIO
        img = PILImage.open(BytesIO(data))
        w, h = img.size
        fmt = img.format.lower() if img.format else ext.lstrip(".")
    except Exception as e:
        return DownloadResult(url=url, status="skipped", error=f"not an image: {e}")

    if w < MIN_DIM or h < MIN_DIM:
        return DownloadResult(url=url, status="skipped",
                              error=f"too small: {w}x{h}")

    # 6. Save
    if pending:
        dest_dir = PENDING_DIR / niche / section
    elif domain:
        dest_dir = DATA_DIR / niche / domain / section
    else:
        dest_dir = DATA_DIR / niche / section
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{sha[:12]}{ext}"
    dest.write_bytes(data)

    return DownloadResult(
        url=url, status="saved",
        file_path=dest,
        sha256=sha,
        width=w, height=h,
        file_size=len(data),
        fmt=fmt,
    )
