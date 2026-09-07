"""File-backed review crawl task queue + state machine."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Terminal vs active statuses for system integration.
TASK_STATUSES = (
    "queued",
    "running",
    "needs_login",
    "softbanned",
    "captcha",
    "done",
    "failed",
    "cancelled",
)

TERMINAL_STATUSES = frozenset(
    {"needs_login", "softbanned", "captcha", "done", "failed", "cancelled"}
)
ACTIVE_STATUSES = frozenset({"queued", "running"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_task_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{uuid.uuid4().hex[:8]}"


@dataclass
class ReviewTask:
    """One ASIN crawl job for the worker / host system."""

    id: str
    asin: str
    site: str = "com"
    account_id: str | None = None
    target: int = 300
    strategy: str = "show_more"
    pace: str = "cautious"
    max_pace: str = "normal"
    max_show_more_clicks: int = 50
    status: str = "queued"
    created_at: str = ""
    updated_at: str = ""
    started_at: str = ""
    finished_at: str = ""
    result_path: str = ""
    log_dir: str = ""
    error: str = ""
    stopped_reason: str = ""
    count: int = 0
    unique_review_ids: int = 0
    show_more_clicks: int = 0
    softbanned: bool = False
    needs_login: bool = False
    captcha: bool = False
    edgex_challenge: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = _utc_now()
        if not self.updated_at:
            self.updated_at = self.created_at
        self.asin = (self.asin or "").strip().upper()
        if self.status not in TASK_STATUSES:
            raise ValueError(f"invalid status: {self.status}")

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewTask":
        allowed = {f.name for f in fields(cls)}
        payload = {k: v for k, v in data.items() if k in allowed}
        if "meta" in payload and payload["meta"] is None:
            payload["meta"] = {}
        return cls(**payload)


class TaskStore:
    """One JSON file per task under ``tasks/``; tiny index for listing."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.dir = self.root / "tasks"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        safe = "".join(c for c in task_id if c.isalnum() or c in "-_.")
        if not safe or safe != task_id:
            raise ValueError(f"invalid task id: {task_id!r}")
        return self.dir / f"{safe}.json"

    def save(self, task: ReviewTask) -> ReviewTask:
        task.updated_at = _utc_now()
        path = self._path(task.id)
        path.write_text(
            json.dumps(task.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return task

    def get(self, task_id: str) -> ReviewTask:
        path = self._path(task_id)
        if not path.exists():
            raise KeyError(f"task not found: {task_id}")
        return ReviewTask.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(
        self,
        *,
        status: str | None = None,
        statuses: Iterable[str] | None = None,
        asin: str | None = None,
        limit: int = 200,
    ) -> list[ReviewTask]:
        want: set[str] | None = None
        if status:
            want = {status}
        elif statuses:
            want = set(statuses)
        items: list[ReviewTask] = []
        for path in sorted(self.dir.glob("*.json"), reverse=True):
            try:
                task = ReviewTask.from_dict(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
            if want and task.status not in want:
                continue
            if asin and task.asin != asin.strip().upper():
                continue
            items.append(task)
            if len(items) >= limit:
                break
        return items

    def create(
        self,
        *,
        asin: str,
        site: str = "com",
        account_id: str | None = None,
        target: int = 300,
        strategy: str = "show_more",
        pace: str = "cautious",
        max_pace: str = "normal",
        max_show_more_clicks: int = 50,
        meta: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> ReviewTask:
        task = ReviewTask(
            id=task_id or _new_task_id(),
            asin=asin,
            site=site,
            account_id=account_id,
            target=target,
            strategy=strategy,
            pace=pace,
            max_pace=max_pace,
            max_show_more_clicks=max_show_more_clicks,
            status="queued",
            meta=dict(meta or {}),
        )
        return self.save(task)

    def transition(
        self,
        task: ReviewTask,
        status: str,
        *,
        error: str = "",
        **fields_update: Any,
    ) -> ReviewTask:
        if status not in TASK_STATUSES:
            raise ValueError(f"invalid status: {status}")
        task.status = status
        if error:
            task.error = error
        for key, value in fields_update.items():
            if not hasattr(task, key):
                raise AttributeError(key)
            setattr(task, key, value)
        if status == "running" and not task.started_at:
            task.started_at = _utc_now()
        if status in TERMINAL_STATUSES and not task.finished_at:
            task.finished_at = _utc_now()
        return self.save(task)

    def claim_next_queued(self) -> ReviewTask | None:
        """Atomically-ish claim oldest queued task (single-worker assumption)."""
        queued = self.list(status="queued", limit=500)
        if not queued:
            return None
        queued.sort(key=lambda t: t.created_at)
        task = queued[0]
        return self.transition(task, "running")
