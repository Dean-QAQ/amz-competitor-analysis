"""Stable Python API for host-system integration (queue + worker)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .accounts import AccountPool
from .auth_playwright import login_and_save
from .fetch import fetch_reviews, save_result
from .tasks import ReviewTask, TaskStore


@dataclass
class RunOutcome:
    task: ReviewTask
    exit_code: int
    """0=done ok; 2=needs human/risk stop; 1=failed."""


class ReviewsService:
    """Programmatic façade: enqueue → worker run → read task/result JSON."""

    def __init__(
        self,
        root: Path | str,
        *,
        pool_path: Path | str | None = None,
        tasks_dir: Path | str | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        pool_file = Path(pool_path) if pool_path else self.root / "accounts" / "pool.json"
        self.pool = AccountPool.load(pool_file, root=self.root)
        self.tasks = TaskStore(self.root)
        if tasks_dir is not None:
            self.tasks.dir = Path(tasks_dir)
            self.tasks.dir.mkdir(parents=True, exist_ok=True)
        (self.root / "data").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_package_root(cls) -> "ReviewsService":
        return cls(Path(__file__).resolve().parent.parent)

    def enqueue(
        self,
        asin: str,
        *,
        site: str = "com",
        account_id: str | None = None,
        target: int = 300,
        strategy: str = "show_more",
        pace: str = "cautious",
        max_pace: str = "normal",
        max_show_more_clicks: int = 50,
        meta: dict[str, Any] | None = None,
    ) -> ReviewTask:
        return self.tasks.create(
            asin=asin,
            site=site,
            account_id=account_id,
            target=target,
            strategy=strategy,
            pace=pace,
            max_pace=max_pace,
            max_show_more_clicks=max_show_more_clicks,
            meta=meta,
        )

    def get_task(self, task_id: str) -> ReviewTask:
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        *,
        status: str | None = None,
        asin: str | None = None,
        limit: int = 200,
    ) -> list[ReviewTask]:
        return self.tasks.list(status=status, asin=asin, limit=limit)

    def login(
        self,
        account_id: str,
        *,
        site: str = "com",
        channel: str = "chrome",
        headed: bool = True,
    ) -> Path:
        account = self.pool.get(account_id)
        if site not in account.sites and "*" not in account.sites:
            account.sites.append(site)
        storage = account.storage_path(self.pool.root)
        profile = account.profile_path(self.pool.root, site)
        login_and_save(
            site=site,
            storage_path=storage,
            profile_dir=profile,
            headed=headed,
            channel=channel,
            account_id=account.id,
            root=self.pool.root,
            auto_wait=True,
        )
        try:
            account.storage_state = str(storage.relative_to(self.root)).replace("\\", "/")
        except ValueError:
            account.storage_state = str(storage)
        account.profile_dir = str(profile)
        account.status = "healthy"
        account.last_error = ""
        self.pool.save()
        # Re-queue tasks blocked on this account/site.
        for task in self.tasks.list(status="needs_login", limit=500):
            if task.site == site and (not task.account_id or task.account_id == account_id):
                self.tasks.transition(task, "queued", error="")
        return storage

    def result_path_for(self, task: ReviewTask) -> Path:
        if task.result_path:
            path = Path(task.result_path)
            return path if path.is_absolute() else self.root / path
        return self.root / "data" / f"reviews_{task.asin}_{task.site}.json"

    def run_task(
        self,
        task_id: str,
        *,
        channel: str = "chrome",
        headed: bool = True,
        resume: bool = True,
    ) -> RunOutcome:
        task = self.tasks.get(task_id)
        if task.status == "running":
            # Allow retry of crashed worker that left status=running.
            pass
        elif task.status not in {"queued", "needs_login"}:
            if task.is_terminal and task.status == "done":
                return RunOutcome(task=task, exit_code=0)
            return RunOutcome(task=task, exit_code=1)

        task = self.tasks.transition(task, "running", error="")
        out = self.result_path_for(task)
        task.result_path = str(out.relative_to(self.root)).replace("\\", "/")
        task.log_dir = "logs"
        self.tasks.save(task)

        try:
            # Block if account still needs login and caller didn't re-login.
            if task.account_id:
                account = self.pool.get(task.account_id)
                if account.status in {"needs_login", "expired"}:
                    task = self.tasks.transition(
                        task,
                        "needs_login",
                        error=f"account {account.id} status={account.status}",
                        needs_login=True,
                    )
                    return RunOutcome(task=task, exit_code=2)

            result = fetch_reviews(
                task.asin,
                site=task.site,
                pool=self.pool,
                account_id=task.account_id,
                target=task.target,
                engine="browser",
                channel=channel,
                headed=headed,
                resume_from=out if resume and out.exists() else None,
                pace_mode=task.pace,
                max_pace=task.max_pace,
                log_dir=self.root / "logs",
                strategy=task.strategy,
                checkpoint_path=out,
                max_show_more_clicks=task.max_show_more_clicks,
            )
            save_result(result, out)

            updates = dict(
                count=result.count,
                unique_review_ids=result.unique_review_ids or result.count,
                show_more_clicks=result.show_more_clicks,
                stopped_reason=result.stopped_reason,
                softbanned=result.softbanned,
                needs_login=result.needs_login,
                captcha=result.captcha,
                edgex_challenge=result.edgex_challenge,
                result_path=str(out.relative_to(self.root)).replace("\\", "/"),
            )

            if result.needs_login:
                task = self.tasks.transition(
                    task, "needs_login", error=result.stopped_reason, **updates
                )
                return RunOutcome(task=task, exit_code=2)
            if result.softbanned:
                task = self.tasks.transition(
                    task, "softbanned", error=result.stopped_reason, **updates
                )
                return RunOutcome(task=task, exit_code=2)
            if result.captcha or result.edgex_challenge:
                task = self.tasks.transition(
                    task,
                    "captcha",
                    error=result.stopped_reason,
                    **updates,
                )
                return RunOutcome(task=task, exit_code=2)

            task = self.tasks.transition(task, "done", error="", **updates)
            return RunOutcome(task=task, exit_code=0)

        except Exception as exc:  # noqa: BLE001
            task = self.tasks.transition(task, "failed", error=str(exc))
            return RunOutcome(task=task, exit_code=1)

    def run_next(
        self,
        *,
        channel: str = "chrome",
        headed: bool = True,
        resume: bool = True,
    ) -> RunOutcome | None:
        claimed = self.tasks.claim_next_queued()
        if claimed is None:
            return None
        # claim_next already set running; run_task will continue from running.
        return self.run_task(
            claimed.id, channel=channel, headed=headed, resume=resume
        )

    def task_snapshot(self, task_id: str) -> dict[str, Any]:
        task = self.get_task(task_id)
        payload = task.to_dict()
        out = self.result_path_for(task)
        payload["result_exists"] = out.exists()
        payload["result_abs"] = str(out)
        return payload
