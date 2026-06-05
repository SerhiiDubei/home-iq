"""
Load and expose config.yaml values throughout HomeIQ.

Usage:
    from homeiq.config import cfg
    print(cfg.niches)
    print(cfg.crawler.max_pages)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
import yaml

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"


@dataclass
class CrawlerConfig:
    max_pages: int = 100
    request_delay: float = 1.5
    min_file_bytes: int = 500
    max_file_bytes: int = 10_485_760
    min_dimension_px: int = 100
    tier1_timeout: int = 30
    tier2_timeout: int = 45
    tier3_timeout: int = 90


@dataclass
class ClassifierConfig:
    openrouter_api_key: str = ""
    model: str = "google/gemini-2.0-flash-exp:free"
    fallback_model: str = "google/gemini-2.5-flash"
    max_concurrent: int = 5
    retry_attempts: int = 3
    cost_per_image_usd: float = 0.0001


@dataclass
class AppConfig:
    niches: list[str] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    exclude_domains: list[str] = field(default_factory=list)
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    classifier: ClassifierConfig = field(default_factory=ClassifierConfig)
    brave_api_key: str = ""
    discovery_max_sites: int = 10
    discovery_skip_crawled: bool = True


def _load() -> AppConfig:
    if not _CONFIG_PATH.exists():
        return AppConfig()
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    crawler_raw = raw.get("crawler", {})
    crawler = CrawlerConfig(
        max_pages=crawler_raw.get("max_pages", 100),
        request_delay=crawler_raw.get("request_delay", 1.5),
        min_file_bytes=crawler_raw.get("min_file_bytes", 500),
        max_file_bytes=crawler_raw.get("max_file_bytes", 10_485_760),
        min_dimension_px=crawler_raw.get("min_dimension_px", 100),
        tier1_timeout=crawler_raw.get("tier1_timeout", 30),
        tier2_timeout=crawler_raw.get("tier2_timeout", 45),
        tier3_timeout=crawler_raw.get("tier3_timeout", 90),
    )

    brave_key = (
        os.environ.get("BRAVE_API_KEY", "")
        or raw.get("discovery", {}).get("brave_api_key", "")
    )
    discovery_max_sites = raw.get("discovery", {}).get("max_sites", 10)
    skip_crawled = raw.get("discovery", {}).get("skip_crawled_domains", True)

    classifier_raw = raw.get("classifier", {})
    classifier = ClassifierConfig(
        openrouter_api_key=(
            os.environ.get("OPENROUTER_API_KEY", "")
            or classifier_raw.get("openrouter_api_key", "")
        ),
        model=classifier_raw.get("model", "google/gemini-2.0-flash-exp:free"),
        fallback_model=classifier_raw.get("fallback_model", "google/gemini-2.5-flash"),
        max_concurrent=classifier_raw.get("max_concurrent", 5),
        retry_attempts=classifier_raw.get("retry_attempts", 3),
        cost_per_image_usd=classifier_raw.get("cost_per_image_usd", 0.0001),
    )

    return AppConfig(
        niches=raw.get("niches", []),
        sections=raw.get("sections", []),
        exclude_domains=raw.get("exclude_domains", []),
        crawler=crawler,
        classifier=classifier,
        brave_api_key=brave_key,
        discovery_max_sites=discovery_max_sites,
        discovery_skip_crawled=skip_crawled,
    )


# Module-level singleton — loaded once on first import
cfg: AppConfig = _load()
