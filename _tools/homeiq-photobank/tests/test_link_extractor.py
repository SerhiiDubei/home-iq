# tests/test_link_extractor.py
import pytest
from homeiq.crawler.link_extractor import extract_links

BASE = "https://www.vivint.com/products/cameras"

def test_extracts_same_domain_links():
    html = '''<html><body>
    <a href="/products/outdoor">outdoor</a>
    <a href="https://www.vivint.com/gallery">gallery</a>
    </body></html>'''
    links = extract_links(html, BASE)
    assert "https://www.vivint.com/products/outdoor" in links
    assert "https://www.vivint.com/gallery" in links

def test_skips_external_links():
    html = '<a href="https://google.com/something">ext</a>'
    links = extract_links(html, BASE)
    assert links == []

def test_skips_blocked_paths():
    html = '''<html><body>
    <a href="/blog/article">blog</a>
    <a href="/careers/engineer">careers</a>
    <a href="/legal/privacy">legal</a>
    <a href="/faq">faq</a>
    </body></html>'''
    links = extract_links(html, BASE)
    assert links == []

def test_strips_anchors_and_querystring():
    html = '<a href="/products/cam?color=black#specs">cam</a>'
    links = extract_links(html, BASE)
    assert links == ["https://www.vivint.com/products/cam"]

def test_deduplicates():
    html = '''<html><body>
    <a href="/products/cam">cam</a>
    <a href="/products/cam">cam again</a>
    </body></html>'''
    links = extract_links(html, BASE)
    assert len(links) == 1

def test_skips_static_assets():
    html = '''<html><body>
    <a href="/style.css">css</a>
    <a href="/script.js">js</a>
    <a href="/image.jpg">img</a>
    <a href="/products/real">real</a>
    </body></html>'''
    links = extract_links(html, BASE)
    assert links == ["https://www.vivint.com/products/real"]

def test_prioritizes_product_paths():
    html = '''<html><body>
    <a href="/about">about</a>
    <a href="/products/cam">cam</a>
    <a href="/gallery/photos">photos</a>
    </body></html>'''
    links = extract_links(html, BASE)
    assert len(links) == 3
    # product/gallery paths come first
    assert links[0] in ["https://www.vivint.com/products/cam",
                         "https://www.vivint.com/gallery/photos"]
    assert links[1] in ["https://www.vivint.com/products/cam",
                         "https://www.vivint.com/gallery/photos"]
    assert links[-1] == "https://www.vivint.com/about"
