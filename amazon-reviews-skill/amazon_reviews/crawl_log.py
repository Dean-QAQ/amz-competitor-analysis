"""Structured crawl logging + performance summary."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CrawlLogger:
    asin: str
    site: str
    account_id: str
    log_dir: Path
    run_id: str = ""
    started_monotonic: float = field(default_factory=time.monotonic)
    events: list[dict[str, Any]] = field(default_factory=list)
    pages_fetched: int = 0
    reviews_start: int = 0
    reviews_end: int = 0
    combos_tried: int = 0
    page_durations_ms: list[float] = field(default_factory=list)
    wait_seconds: list[float] = field(default_factory=list)
    mode_changes: list[dict[str, Any]] = field(default_factory=list)
    risk_events: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.log_dir = Path(self.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if not self.run_id:
            self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.jsonl_path = self.log_dir / f"fetch_{self.asin}_{self.site}_{self.run_id}.jsonl"
        self.summary_path = self.log_dir / f"fetch_{self.asin}_{self.site}_{self.run_id}_summary.json"
        self.log(
            "run_start",
            asin=self.asin,
            site=self.site,
            account_id=self.account_id,
            run_id=self.run_id,
        )

    def log(self, event: str, **payload: Any) -> None:
        row = {
            "ts": _utc_now(),
            "event": event,
            "elapsed_s": round(time.monotonic() - self.started_monotonic, 3),
            **payload,
        }
        self.events.append(row)
        with self.jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        # Mirror important events to console.
        if event in {
            "run_start",
            "run_end",
            "page_done",
            "progress",
            "mode_change",
            "risk",
            "captcha",
            "session_cooldown",
            "combo_start",
        }:
            nice = " ".join(f"{k}={v}" for k, v in payload.items() if k not in {"html_snippet"})
            print(f"[log] {event} {nice}".strip(), flush=True)

    def pace_event(self, event: str, payload: dict[str, Any]) -> None:
        if event == "mode_change":
            self.mode_changes.append({"ts": _utc_now(), **payload})
        if event in {"risk", "captcha_backoff"}:
            self.risk_events.append({"ts": _utc_now(), "event": event, **payload})
        if "delay_s" in payload:
            self.wait_seconds.append(float(payload["delay_s"]))
        if "waited_s" in payload:
            self.wait_seconds.append(float(payload["waited_s"]))
        self.log(event, **payload)

    def note_page(
        self,
        *,
        duration_ms: float,
        new_reviews: int,
        total_reviews: int,
        pace_mode: str,
        url: str,
        health: str,
    ) -> None:
        self.pages_fetched += 1
        self.page_durations_ms.append(duration_ms)
        self.log(
            "page_done",
            duration_ms=round(duration_ms, 1),
            new_reviews=new_reviews,
            total_reviews=total_reviews,
            pace_mode=pace_mode,
            health=health,
            url=url[:180],
        )

    def finish(self, *, result: dict[str, Any]) -> Path:
        elapsed = max(time.monotonic() - self.started_monotonic, 0.001)
        gained = max(self.reviews_end - self.reviews_start, 0)
        avg_page_ms = (
            sum(self.page_durations_ms) / len(self.page_durations_ms)
            if self.page_durations_ms
            else 0.0
        )
        avg_wait_s = (
            sum(self.wait_seconds) / len(self.wait_seconds) if self.wait_seconds else 0.0
        )
        summary = {
            "run_id": self.run_id,
            "asin": self.asin,
            "site": self.site,
            "account_id": self.account_id,
            "started_at": self.events[0]["ts"] if self.events else _utc_now(),
            "finished_at": _utc_now(),
            "elapsed_s": round(elapsed, 2),
            "reviews_start": self.reviews_start,
            "reviews_end": self.reviews_end,
            "reviews_gained": gained,
            "pages_fetched": self.pages_fetched,
            "combos_tried": self.combos_tried,
            "reviews_per_hour": round(gained / elapsed * 3600, 2),
            "pages_per_hour": round(self.pages_fetched / elapsed * 3600, 2),
            "avg_page_fetch_ms": round(avg_page_ms, 1),
            "avg_wait_s": round(avg_wait_s, 2),
            "total_wait_s": round(sum(self.wait_seconds), 2),
            "mode_changes": self.mode_changes,
            "risk_events": self.risk_events,
            "result": {
                "count": result.get("count"),
                "target": result.get("target"),
                "stopped_reason": result.get("stopped_reason"),
                "softbanned": result.get("softbanned"),
                "needs_login": result.get("needs_login"),
                "captcha": result.get("captcha"),
                "edgex_challenge": result.get("edgex_challenge"),
                "pagination_disabled": result.get("pagination_disabled"),
            },
            "jsonl": str(self.jsonl_path),
        }
        self.summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.log("run_end", **{k: v for k, v in summary.items() if k not in {"mode_changes", "risk_events", "result"}})
        print(f"[log] summary -> {self.summary_path}", flush=True)
        return self.summary_path
