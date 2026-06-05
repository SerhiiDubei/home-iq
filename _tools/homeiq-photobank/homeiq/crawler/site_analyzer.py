"""
Analyze a reference website to determine its niche and keywords.

Usage:
    from homeiq.crawler.site_analyzer import analyze_html, analyze_url, AnalysisResult
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import logging

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

# Maps niche name → list of keywords to look for in title/meta/h1
_NICHE_MAP: dict[str, list[str]] = {
    "bathroom":  ["bathroom", "bathtub", "bath fitter", "tub replacement", "shower remodel"],
    "security":  ["security", "alarm", "camera", "smart home", "surveillance", "vivint", "adt"],
    "siding":    ["siding", "hardie", "cladding", "exterior panel", "vinyl siding"],
    "roofing":   ["roof", "roofing", "shingle"],
    "hvac":      ["hvac", "heating", "cooling", "furnace", "air conditioning", "heat pump"],
    "flooring":  ["flooring", "hardwood", "laminate", "tile floor", "carpet"],
    "kitchen":   ["kitchen", "cabinet", "countertop", "kitchen remodel"],
    "solar":     ["solar", "photovoltaic", "solar panel", "solar installation"],
    "windows":   ["window", "replacement window", "double pane", "window installation"],
    "gutter":    ["gutter", "leafguard", "eavestrough", "gutter guard"],
    "plumbing":  ["plumbing", "plumber", "pipe", "drain", "water heater"],
    "walk_in_tubs": ["walk-in tub", "walk in tub", "walkin tub", "accessible tub"],
}


@dataclass
class AnalysisResult:
    niche: str
    keywords: list[str] = field(default_factory=list)
    title: str = ""


def analyze_html(html: str, url: str) -> AnalysisResult:
    """
    Parse HTML and determine niche + keywords.
    Falls back to domain name if no niche matched.
    """
    soup = BeautifulSoup(html, "lxml")

    title = soup.find("title")
    title_text = title.get_text(strip=True) if title else ""

    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_text = meta_desc.get("content", "") if meta_desc else ""

    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else ""

    combined = f"{title_text} {meta_text} {h1_text}".lower()

    detected_niche: Optional[str] = None
    matched_keywords: list[str] = []

    for niche, keywords in _NICHE_MAP.items():
        hits = [kw for kw in keywords if kw in combined]
        if hits:
            detected_niche = niche
            matched_keywords = hits
            break

    if not detected_niche:
        domain = urlparse(url).netloc.removeprefix("www.")
        # Also check if domain name itself contains a niche keyword
        # e.g. "vivint.com" → contains "vivint" which is in security keywords
        domain_lower = domain.lower()
        for niche, keywords in _NICHE_MAP.items():
            hits = [kw for kw in keywords if kw in domain_lower]
            if hits:
                detected_niche = niche
                matched_keywords = hits
                break
        if not detected_niche:
            detected_niche = domain
            words = re.findall(r'\b[a-z]{4,}\b', combined)
            matched_keywords = list(dict.fromkeys(words))[:3]

    kw_list = list(dict.fromkeys([detected_niche.replace("_", " ")] + matched_keywords))[:3]

    return AnalysisResult(
        niche=detected_niche,
        keywords=kw_list,
        title=title_text,
    )


# --- Contractor vs news/review site validator ---

_CONTRACTOR_SIGNALS = [
    "free quote", "get a quote", "request a quote", "get quote",
    "free estimate", "get estimate", "free consultation",
    "schedule", "book now", "contact us", "service area",
    "our technicians", "our installers", "our crew",
    "licensed", "insured", "bonded", "warranty",
    "call us", "call today",
]

_NEWS_SIGNALS = [
    "editorial", "staff writer", "editor at large", "journalist",
    "best of", "our top picks", "our picks", "ranking",
    "we tested", "we reviewed", "affiliate",
    "advertiser disclosure", "editorial team",
]


def is_contractor_site(html: str) -> bool:
    """
    Returns True if this homepage looks like a contractor/service company.
    Returns False if it looks like a news, review, or media site.

    Heuristic: count contractor vs news signals in lowercased HTML.
    Passes if contractor_hits >= 2 and news_hits <= 1.
    """
    text = html.lower()
    contractor_hits = sum(1 for s in _CONTRACTOR_SIGNALS if s in text)
    news_hits = sum(1 for s in _NEWS_SIGNALS if s in text)
    return contractor_hits >= 2 and news_hits <= 1


async def analyze_url(url: str) -> AnalysisResult:
    """
    Fetch URL and analyze it. Uses httpx directly — only needs title/meta/h1.
    Falls back to domain-only analysis if the site blocks the request (403/429).
    """
    html = ""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
                "Accept": "text/html,*/*",
            })
            r.raise_for_status()
            html = r.text
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        log.debug("analyze_url fetch failed (%s), falling back to domain analysis: %s", type(e).__name__, url)
        # Fall back to empty HTML — analyze_html will use domain as niche
    return analyze_html(html, url)
