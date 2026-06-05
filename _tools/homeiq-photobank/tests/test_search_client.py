"""Tests for search_client — DuckDuckGo scraper."""
import pytest
from homeiq.crawler.search_client import build_queries, filter_urls, SearchClient, _parse_ddg_results

def test_build_queries_returns_three():
    queries = build_queries(["bathroom remodeling", "tub replacement"])
    assert len(queries) == 3
    assert all("bathroom remodeling" in q or "tub replacement" in q for q in queries)

def test_build_queries_includes_keyword():
    queries = build_queries(["solar installation"])
    combined = " ".join(queries)
    assert "solar installation" in combined

def test_filter_urls_removes_excluded():
    exclude = {"pinterest.com", "houzz.com"}
    urls = [
        "https://www.pinterest.com/bathroom",
        "https://www.rebath.com/",
        "https://houzz.com/photos",
        "https://bathplanet.com/",
    ]
    result = filter_urls(urls, exclude_domains=exclude, crawled_domains=set())
    assert "https://www.rebath.com/" in result
    assert "https://bathplanet.com/" in result
    assert all("pinterest.com" not in u for u in result)
    assert all("houzz.com" not in u for u in result)

def test_filter_urls_removes_already_crawled():
    urls = ["https://rebath.com/", "https://bathfitter.com/"]
    result = filter_urls(urls, exclude_domains=set(), crawled_domains={"rebath.com"})
    assert "https://bathfitter.com/" in result
    assert all("rebath.com" not in u for u in result)

def test_filter_urls_deduplicates_by_domain():
    urls = [
        "https://rebath.com/",
        "https://rebath.com/about",
        "https://bathplanet.com/",
    ]
    result = filter_urls(urls, exclude_domains=set(), crawled_domains=set())
    domains = [u.split("/")[2] for u in result]
    assert len(domains) == len(set(domains))

def test_search_client_no_api_key_needed():
    # DDG requires no API key — SearchClient() constructs without error
    client = SearchClient()
    assert client is not None
    client2 = SearchClient(api_key="")
    assert client2 is not None

def test_parse_ddg_results_extracts_urls():
    html = """
    <html><body>
      <a class="result__a" href="https://rebath.com/gallery">Re-Bath Gallery</a>
      <a class="result__a" href="https://bathplanet.com/">Bath Planet</a>
      <a class="result__a" href="/l/?uddg=https%3A%2F%2Fexample.com%2F&rut=abc">Encoded</a>
    </body></html>
    """
    urls = _parse_ddg_results(html)
    assert "https://rebath.com/gallery" in urls
    assert "https://bathplanet.com/" in urls
