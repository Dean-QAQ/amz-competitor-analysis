from __future__ import annotations

from pathlib import Path

from amazon_reviews.parser import parse_reviews
from amazon_reviews.sites import get_site
from amazon_reviews.softban import assess_review_page

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_reviews_ok():
    html = (FIXTURES / "reviews_ok.html").read_text(encoding="utf-8")
    reviews = parse_reviews(
        html,
        asin="B0DB142C6Y",
        site="com",
        source_url="https://www.amazon.com/product-reviews/B0DB142C6Y",
        sort_by="recent",
        filter_star=None,
    )
    assert len(reviews) == 2
    assert reviews[0].review_id == "R1TESTAAA001"
    assert reviews[0].rating == 5.0
    assert "Great nightstand" in reviews[0].title
    assert reviews[0].verified is True
    assert reviews[0].helpful_votes == 12
    assert reviews[1].helpful_votes == 1
    assert reviews[1].verified is False


def test_softban_detected():
    html = (FIXTURES / "reviews_softban.html").read_text(encoding="utf-8")
    health = assess_review_page(html)
    assert health.softbanned is True
    assert health.ok is False


def test_edgex_detected():
    html = (
        "<html><body><div>Getting things ready...</div>"
        "<script>location='/edgex/guard/rx'</script></body></html>"
    )
    health = assess_review_page(html)
    assert health.edgex_challenge is True
    assert health.ok is False


def test_edgex_not_false_positive_on_rx_script():
    html = "<html><body><script>window.rx={}</script><div data-hook='review' id='R1'></div></body></html>"
    health = assess_review_page(html)
    assert health.edgex_challenge is False
    assert health.review_count_on_page == 1


def test_ok_page_health():
    html = (FIXTURES / "reviews_ok.html").read_text(encoding="utf-8")
    health = assess_review_page(html)
    assert health.ok is True
    assert health.softbanned is False
    assert health.review_count_on_page == 2
    assert health.has_pagination is True


def test_reviews_url_matrix():
    site = get_site("com")
    url = site.reviews_url(
        "B0DB142C6Y",
        page=2,
        sort_by="helpful",
        filter_by_star="one_star",
        keyword="drawer",
    )
    assert "product-reviews/B0DB142C6Y" in url
    assert "pageNumber=2" in url
    assert "sortBy=helpful" in url
    assert "filterByStar=one_star" in url
    assert "filterByKeyword=drawer" in url


def test_site_aliases():
    assert get_site("amazon.com").code == "com"
    assert get_site(".de").code == "de"
