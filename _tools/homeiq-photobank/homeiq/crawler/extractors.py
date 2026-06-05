"""Image extractors for HomeIQ crawler."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, replace as dc_replace
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ImageRef:
    url: str
    alt_text: Optional[str] = None
    width_hint: Optional[int] = None
    height_hint: Optional[int] = None
    parent_section: Optional[str] = None
    source_attr: Optional[str] = None


class ImageExtractor(ABC):
    @abstractmethod
    def extract(self, soup: BeautifulSoup, base_url: str) -> list[ImageRef]: ...


def _abs(url: str, base: str) -> str:
    if not url or url.startswith("data:"):
        return ""
    return urljoin(base, url.strip())


def _int_attr(tag, attr: str) -> Optional[int]:
    val = tag.get(attr)
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None


_CSS_URL_WRAP_RE = re.compile(r'^url\(\s*["\']?(.+?)["\']?\s*\)$', re.IGNORECASE)


def _unwrap_css_url(val: str) -> str:
    """Strip url(...) wrapper if present, e.g. url('/img/hero.jpg') -> /img/hero.jpg"""
    m = _CSS_URL_WRAP_RE.match(val)
    return m.group(1) if m else val


def _parse_srcset(srcset: str) -> Optional[tuple[str, Optional[int]]]:
    """Return (best_url, width_hint) from srcset string, preferring largest w descriptor."""
    candidates_w: list[tuple[int, str]] = []
    candidates_x: list[tuple[float, str]] = []
    fallback: Optional[str] = None

    for part in srcset.split(","):  # naïve split; URLs with literal commas would be mishandled
        tokens = part.strip().split()
        if not tokens:
            continue
        url = tokens[0]
        if url.startswith("data:"):
            continue
        desc = tokens[1] if len(tokens) > 1 else ""
        if desc.endswith("w"):
            try:
                candidates_w.append((int(desc[:-1]), url))
            except ValueError:
                continue
        elif desc.endswith("x"):
            try:
                candidates_x.append((float(desc[:-1]), url))
            except ValueError:
                continue
        else:
            if fallback is None:
                fallback = url

    if candidates_w:
        best_w, best_url = max(candidates_w, key=lambda c: c[0])
        return best_url, best_w
    if candidates_x:
        _, best_url = max(candidates_x, key=lambda c: c[0])
        return best_url, None
    if fallback:
        return fallback, None
    return None


class PictureSrcsetExtractor(ImageExtractor):
    def extract(self, soup: BeautifulSoup, base_url: str) -> list[ImageRef]:
        results = []
        for picture in soup.find_all("picture"):
            ref = self._from_picture(picture, base_url)
            if ref:
                results.append(ref)
        return results

    def _from_picture(self, picture, base_url: str) -> Optional[ImageRef]:
        img = picture.find("img")
        # alt from <img> or data-alt on <picture> (lozad pattern)
        alt = None
        if img:
            alt = img.get("alt") or None
        if not alt:
            alt = picture.get("data-alt") or None

        parent_section = _detect_section_from_tag(picture)

        for source in picture.find_all("source"):
            srcset = source.get("srcset", "")
            if not srcset:
                continue
            parsed = _parse_srcset(srcset)
            if parsed:
                url, width = parsed
                abs_url = _abs(url, base_url)
                if abs_url:
                    return ImageRef(url=abs_url, alt_text=alt,
                                    width_hint=width, source_attr="srcset",
                                    parent_section=parent_section)

        # lozad: no <img> inside, but data-iesrc on <picture>
        iesrc = picture.get("data-iesrc", "")
        if iesrc:
            abs_url = _abs(iesrc, base_url)
            if abs_url:
                return ImageRef(url=abs_url, alt_text=alt, source_attr="data-iesrc",
                                parent_section=parent_section)

        if img:
            src = img.get("src", "")
            abs_url = _abs(src, base_url)
            if abs_url:
                return ImageRef(
                    url=abs_url, alt_text=alt,
                    width_hint=_int_attr(img, "width"),
                    height_hint=_int_attr(img, "height"),
                    source_attr="src",
                    parent_section=parent_section,
                )
        return None


# ---------------------------------------------------------------------------
# Stubs – to be implemented in subsequent tasks
# ---------------------------------------------------------------------------

_DATA_ATTRS = [
    "data-srcset", "data-src", "data-lazy-src", "data-lazy",
    "data-original", "data-img-src", "data-bg", "data-url",
    "data-iesrc",   # lozad lazy loader (Vivint, Drupal sites)
    "data-image", "data-photo", "data-thumb",
]


class DataSrcExtractor(ImageExtractor):
    def extract(self, soup: BeautifulSoup, base_url: str) -> list[ImageRef]:
        results = []
        for img in soup.find_all("img"):
            ref = self._from_img(img, base_url)
            if ref:
                results.append(ref)
        return results

    def _from_img(self, img, base_url: str) -> Optional[ImageRef]:
        parent_section = _detect_section_from_tag(img)
        for attr in _DATA_ATTRS:
            val = img.get(attr, "").strip()
            if not val:
                continue
            val = _unwrap_css_url(val)
            if not val:
                continue
            if attr == "data-srcset":
                parsed = _parse_srcset(val)
                if parsed:
                    url, width = parsed
                    abs_url = _abs(url, base_url)
                    if abs_url:
                        return ImageRef(url=abs_url, alt_text=img.get("alt") or None,
                                        width_hint=width, source_attr=attr,
                                        parent_section=parent_section)
            else:
                abs_url = _abs(val, base_url)
                if abs_url:
                    return ImageRef(url=abs_url, alt_text=img.get("alt") or None,
                                    source_attr=attr, parent_section=parent_section)
        return None


_CSS_BG_INLINE_RE = re.compile(r'url\(\s*["\']?([^"\')\s]+)["\']?\s*\)')
_CSS_BG_DECL_RE = re.compile(
    r'background(?:-image)?\s*:[^;]*url\(\s*["\']?([^"\')\s]+)["\']?\s*\)',
    re.IGNORECASE,
)


class CSSBackgroundExtractor(ImageExtractor):
    def extract(self, soup: BeautifulSoup, base_url: str) -> list[ImageRef]:
        results = []

        for tag in soup.find_all(style=True):
            style = tag.get("style", "")
            if "background" not in style.lower():
                continue
            for m in _CSS_BG_INLINE_RE.finditer(style):
                abs_url = _abs(m.group(1), base_url)
                if abs_url:
                    results.append(ImageRef(url=abs_url, source_attr="bg-css"))

        for style_tag in soup.find_all("style"):
            css_text = style_tag.get_text()
            for m in _CSS_BG_DECL_RE.finditer(css_text):
                abs_url = _abs(m.group(1), base_url)
                if abs_url:
                    results.append(ImageRef(url=abs_url, source_attr="bg-css"))

        return results


class PlainImgSrcExtractor(ImageExtractor):
    def extract(self, soup: BeautifulSoup, base_url: str) -> list[ImageRef]:
        results = []
        for img in soup.find_all("img"):
            src = img.get("src", "").strip()
            abs_url = _abs(src, base_url)
            if not abs_url:
                continue
            parent_section = _detect_section_from_tag(img)
            results.append(ImageRef(
                url=abs_url,
                alt_text=img.get("alt") or None,
                width_hint=_int_attr(img, "width"),
                height_hint=_int_attr(img, "height"),
                source_attr="src",
                parent_section=parent_section,
            ))
        return results


# Section keywords for HTML parent context inspection
_SECTION_HTML_HINTS = {
    "hero":         ["hero", "banner", "header", "jumbotron", "masthead",
                     "splash", "cover", "main-image", "intro", "lead",
                     "featured", "showcase", "top-section", "page-hero",
                     "site-header", "header-image"],
    "before_after": ["before", "after", "before-after", "transformation",
                     "compare", "comparison", "ba-", "-ba-", "slider",
                     "reveal", "makeover", "split"],
    "project":      ["project", "portfolio", "gallery", "work", "job",
                     "result", "finished", "completed", "done", "case",
                     "showcase", "example", "our-work", "recent-work",
                     "case-study"],
    "finished":     ["finished", "complete", "final", "done",
                     "after-photo", "completed-project"],
}


def _detect_section_from_tag(tag) -> Optional[str]:
    """
    Walk up the DOM from `tag` (up to 5 ancestors), collect class names,
    IDs, and aria-labels. Return the first matching section, or None.
    """
    context_parts: list[str] = []
    node = tag
    for _ in range(5):
        if node is None or not hasattr(node, "get"):
            break
        cls = " ".join(node.get("class", []) or []).lower()
        node_id = (node.get("id") or "").lower()
        aria = (node.get("aria-label") or "").lower()
        context_parts.extend([cls, node_id, aria])
        node = getattr(node, "parent", None)

    context = " ".join(filter(None, context_parts))
    if not context:
        return None

    for section, keywords in _SECTION_HTML_HINTS.items():
        if any(kw in context for kw in keywords):
            return section
    return None


_CLOUDINARY_SIZE_RE = re.compile(r'(?<=[,/])([wh]_)\d+(?=[,/])')


def _cloudinary_transform(refs: list[ImageRef]) -> list[ImageRef]:
    result = []
    for ref in refs:
        if "res.cloudinary.com" not in ref.url:
            result.append(ref)
            continue
        new_url = _CLOUDINARY_SIZE_RE.sub(
            lambda m: "w_1200" if m.group(1) == "w_" else "h_900", ref.url
        )
        if new_url != ref.url:
            new_width = 1200 if "w_1200" in new_url else ref.width_hint
            new_height = 900 if "h_900" in new_url else ref.height_hint
            ref = dc_replace(ref, url=new_url, width_hint=new_width, height_hint=new_height)
        result.append(ref)
    return result


_EXTRACTORS: list[ImageExtractor] = [
    PictureSrcsetExtractor(),
    DataSrcExtractor(),
    CSSBackgroundExtractor(),
    PlainImgSrcExtractor(),
]


def extract_images(html: str, base_url: str) -> list[ImageRef]:
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return []

    all_refs: list[ImageRef] = []
    for extractor in _EXTRACTORS:
        try:
            all_refs.extend(extractor.extract(soup, base_url))
        except Exception:
            pass

    seen: set[str] = set()
    deduped: list[ImageRef] = []
    for ref in all_refs:
        if ref.url not in seen:
            seen.add(ref.url)
            deduped.append(ref)

    return _cloudinary_transform(deduped)
