"""Tests for site_analyzer — niche detection from page HTML."""
import pytest
from homeiq.crawler.site_analyzer import analyze_html, AnalysisResult, is_contractor_site

def test_bathroom_detected():
    html = "<html><head><title>Bath Fitter - Bathroom Remodeling</title></head><body><h1>Transform your bathroom</h1></body></html>"
    result = analyze_html(html, "https://bathfitter.com/")
    assert result.niche == "bathroom"
    assert "bathroom" in result.keywords

def test_security_detected():
    html = "<html><head><title>Vivint Smart Home Security Systems</title></head><body><h1>Home security cameras and alarm systems</h1></body></html>"
    result = analyze_html(html, "https://vivint.com/")
    assert result.niche == "security"

def test_unknown_niche_falls_back_to_domain():
    html = "<html><head><title>Acme Corp</title></head><body></body></html>"
    result = analyze_html(html, "https://acmecorp.com/")
    assert result.niche == "acmecorp.com"

def test_keywords_not_empty():
    html = "<html><head><title>Solar Panel Installation</title><meta name='description' content='Professional solar installation services'></head><body></body></html>"
    result = analyze_html(html, "https://solarpros.com/")
    assert result.niche == "solar"
    assert "solar" in result.keywords

def test_analysis_result_has_title():
    html = "<html><head><title>James Hardie Siding Products</title></head><body></body></html>"
    result = analyze_html(html, "https://jameshardie.com/")
    assert result.title == "James Hardie Siding Products"
    assert result.niche == "siding"

def test_www_prefix_stripped_by_removeprefix():
    """www.window-world.com must not be corrupted by lstrip — niche should match 'windows'."""
    html = "<html><head><title>Window World Replacement Windows</title></head></html>"
    result = analyze_html(html, "https://www.window-world.com/")
    assert result.niche == "windows", f"Expected 'windows', got '{result.niche}'"


# --- is_contractor_site tests ---

def test_contractor_site_passes():
    html = """
    <html><body>
      <h1>Home Security Installation</h1>
      <p>Get a free quote today. Licensed and insured technicians.</p>
      <a href="/contact">Contact Us</a>
      <p>Service area covers all of Texas. Call us today!</p>
    </body></html>
    """
    assert is_contractor_site(html) is True


def test_news_site_rejected():
    html = """
    <html><body>
      <h1>Best Home Security Systems of 2024</h1>
      <p>Our editorial team reviewed the top picks. Advertiser disclosure.</p>
      <p>We tested 15 systems. Our top picks are ranked by our staff writer.</p>
    </body></html>
    """
    assert is_contractor_site(html) is False


def test_contractor_site_with_too_few_signals_defaults_include():
    """A sparse page with no signals — contractor_hits=0, news_hits=0 → fails (< 2)."""
    html = "<html><body><p>Welcome to our company.</p></body></html>"
    # 0 contractor hits < 2 → returns False; but we include on fetch-error in validator
    assert is_contractor_site(html) is False


def test_fetch_error_site_included_by_default():
    """Validator includes site when fetch fails (html='') — is_contractor_site not called."""
    # Empty HTML: 0 contractor hits → fails; but in SearchClient._validate_sites
    # we include by default when html is empty (fetch error path)
    # This test confirms the heuristic threshold behavior directly:
    assert is_contractor_site("") is False  # empty → fails heuristic, but validator uses include-on-error
