"""
Section detector — classifies an ImageRef into one of:
  hero / before_after / project / finished / unknown

Priority:
  1. parent_section from HTML context (set by extractors)
  2. URL keyword matching
  3. alt_text keyword matching
  4. fallback: "unknown"
"""
from __future__ import annotations
from homeiq.crawler.extractors import ImageRef

_URL_HINTS = {
    "hero":         ["hero", "banner", "header", "cover", "main-image",
                     "splash", "masthead", "featured", "page-hero"],
    "before_after": ["before", "after", "ba_", "_ba_", "before-after",
                     "before_after", "transformation", "comparison"],
    "project":      ["project", "portfolio", "gallery", "work", "job",
                     "result", "finished", "completed", "case-study",
                     "our-work"],
    "finished":     ["finished", "complete", "final", "done", "after-photo"],
}


def detect_section(ref: ImageRef) -> str:
    """Return the best section tag for this ImageRef."""
    # 1. HTML context wins
    if ref.parent_section:
        return ref.parent_section

    # 2. URL keywords
    url_lower = ref.url.lower()
    for section, keywords in _URL_HINTS.items():
        if any(kw in url_lower for kw in keywords):
            return section

    # 3. Alt text keywords
    if ref.alt_text:
        alt_lower = ref.alt_text.lower()
        for section, keywords in _URL_HINTS.items():
            if any(kw in alt_lower for kw in keywords):
                return section

    return "unknown"
