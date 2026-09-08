"""Tests for task state machine (no browser)."""

from __future__ import annotations

from pathlib import Path

import pytest

from amazon_reviews.tasks import ReviewTask, TaskStore, TERMINAL_STATUSES


def test_task_store_create_get_list(tmp_path: Path) -> None:
    store = TaskStore(tmp_path)
    t1 = store.create(asin="B0AAA", site="com", target=10)
    assert t1.status == "queued"
    t2 = store.create(asin="B0BBB", site="com")
    got = store.get(t1.id)
    assert got.asin == "B0AAA"
    listed = store.list(status="queued")
    assert {x.id for x in listed} == {t1.id, t2.id}


def test_claim_and_terminal_transition(tmp_path: Path) -> None:
    store = TaskStore(tmp_path)
    store.create(asin="B0CCC")
    claimed = store.claim_next_queued()
    assert claimed is not None
    assert claimed.status == "running"
    assert store.claim_next_queued() is None
    done = store.transition(claimed, "done", count=12, unique_review_ids=12)
    assert done.status in TERMINAL_STATUSES
    assert done.finished_at
    assert done.count == 12


def test_invalid_status_rejected() -> None:
    with pytest.raises(ValueError):
        ReviewTask(id="x", asin="B0X", status="nope")
