"""Ensure reported counts are unique review_id based."""

from __future__ import annotations

from amazon_reviews.fetch import FetchResult
from amazon_reviews.parser import Review


def test_fetch_result_count_and_unique_ids() -> None:
    result = FetchResult(asin="B0TEST", site="com", account_id="a", target=10)
    for rid in ("R1", "R2", "R1", "R3"):
        if any(r.review_id == rid for r in result.reviews):
            continue
        result.reviews.append(
            Review(
                review_id=rid,
                asin="B0TEST",
                site="com",
                title="t",
                body="b",
                rating=5.0,
                date_text="",
                author="",
                verified=False,
                helpful_votes=None,
                variant="",
                source_url="",
                filter_star=None,
                sort_by="recent",
            )
        )
    d = result.to_dict()
    assert d["count"] == 3
    assert d["unique_review_ids"] == 3
