"""Tests for ReviewsService wiring without browser (mock fetch)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from amazon_reviews.api import ReviewsService
from amazon_reviews.fetch import FetchResult
from amazon_reviews.parser import Review


def _write_pool(root: Path) -> Path:
    pool = root / "accounts" / "pool.json"
    pool.parent.mkdir(parents=True, exist_ok=True)
    pool.write_text(
        json.dumps(
            {
                "accounts": [
                    {
                        "id": "acc1",
                        "label": "t",
                        "sites": ["com"],
                        "enabled": True,
                        "status": "healthy",
                        "storage_state": "accounts/storage/acc1.com.json",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return pool


def test_enqueue_and_run_task_done(tmp_path: Path) -> None:
    pool = _write_pool(tmp_path)
    svc = ReviewsService(tmp_path, pool_path=pool)
    task = svc.enqueue("b0testasin", account_id="acc1", target=2)

    fake = FetchResult(
        asin="B0TESTASIN",
        site="com",
        account_id="acc1",
        target=2,
        strategy="show_more",
    )
    fake.reviews = [
        Review(
            review_id="R1",
            asin="B0TESTASIN",
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
        ),
        Review(
            review_id="R2",
            asin="B0TESTASIN",
            site="com",
            title="t2",
            body="b2",
            rating=4.0,
            date_text="",
            author="",
            verified=False,
            helpful_votes=None,
            variant="",
            source_url="",
            filter_star=None,
            sort_by="recent",
        ),
    ]
    fake.stopped_reason = "reached_target_2"
    fake.unique_review_ids = 2

    with patch("amazon_reviews.api.fetch_reviews", return_value=fake):
        outcome = svc.run_task(task.id)

    assert outcome.exit_code == 0
    assert outcome.task.status == "done"
    assert outcome.task.count == 2
    assert svc.result_path_for(outcome.task).exists()


def test_run_task_needs_login_exit_2(tmp_path: Path) -> None:
    pool = _write_pool(tmp_path)
    svc = ReviewsService(tmp_path, pool_path=pool)
    task = svc.enqueue("B0LOGIN", account_id="acc1", target=5)
    fake = FetchResult(
        asin="B0LOGIN",
        site="com",
        account_id="acc1",
        target=5,
    )
    fake.needs_login = True
    fake.stopped_reason = "login wall / session expired"

    with patch("amazon_reviews.api.fetch_reviews", return_value=fake):
        outcome = svc.run_task(task.id)

    assert outcome.exit_code == 2
    assert outcome.task.status == "needs_login"
