"""Smoke tests for discover_sites CLI."""
import pytest
from homeiq.cli.discover_sites import build_site_list, format_summary

def test_build_site_list_includes_reference():
    reference = "https://bathfitter.com/"
    found = ["https://rebath.com/", "https://bathplanet.com/"]
    result = build_site_list(reference, found)
    assert result[0] == reference  # reference сайт завжди перший
    assert "https://rebath.com/" in result
    assert "https://bathplanet.com/" in result

def test_build_site_list_no_duplicates():
    reference = "https://bathfitter.com/"
    # found contains same domain as reference
    found = ["https://bathfitter.com/about", "https://rebath.com/"]
    result = build_site_list(reference, found)
    # bathfitter.com повинен бути один раз
    bathfitter_count = sum(1 for u in result if "bathfitter.com" in u)
    assert bathfitter_count == 1

def test_format_summary():
    stats = [
        {"url": "https://bathfitter.com/", "saved": 119, "pages": 20},
        {"url": "https://rebath.com/", "saved": 87, "pages": 20},
    ]
    summary = format_summary(stats)
    assert "2 sites" in summary
    assert "206" in summary  # total photos
