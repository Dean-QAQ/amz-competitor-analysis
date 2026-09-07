#!/usr/bin/env python3
"""Tiny CLI bridge for amz-competitor-analysis Node server ↔ amazon-reviews-skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SITE_MAP = {
    "US": "com",
    "UK": "co.uk",
    "DE": "de",
    "FR": "fr",
    "IT": "it",
    "ES": "es",
    "JP": "co.jp",
    "CA": "ca",
    "AU": "com.au",
    "MX": "com.mx",
    "IN": "in",
}


def _skill_root() -> Path:
    # amz-competitor-analysis/scripts -> ../../amazon-reviews-skill
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent.parent / "amazon-reviews-skill",
        here.parent / "amazon-reviews-skill",
        Path.cwd().parent / "amazon-reviews-skill",
        Path.cwd() / "amazon-reviews-skill",
    ]
    for path in candidates:
        if (path / "amazon_reviews" / "api.py").exists():
            return path.resolve()
    raise SystemExit(json.dumps({"ok": False, "error": "amazon-reviews-skill not found"}, ensure_ascii=False))


def _svc(skill_root: Path):
    sys.path.insert(0, str(skill_root))
    from amazon_reviews.api import ReviewsService  # noqa: WPS433

    return ReviewsService(skill_root)


def _site_code(value: str) -> str:
    raw = (value or "com").strip()
    return SITE_MAP.get(raw.upper(), raw.lower().lstrip("."))


def cmd_enqueue(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).resolve() if args.skill_root else _skill_root()
    svc = _svc(skill_root)
    site = _site_code(args.site)
    task = svc.enqueue(
        args.asin,
        site=site,
        account_id=args.account or None,
        target=int(args.target),
        strategy=args.strategy,
        pace=args.pace,
        max_pace=args.max_pace,
        meta={"source": "amz-competitor-analysis", "marketplace": args.site},
    )
    print(json.dumps({"ok": True, "task": task.to_dict(), "skillRoot": str(skill_root)}, ensure_ascii=False))
    return 0


def cmd_task(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).resolve() if args.skill_root else _skill_root()
    svc = _svc(skill_root)
    snap = svc.task_snapshot(args.id)
    print(json.dumps({"ok": True, "task": snap}, ensure_ascii=False))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).resolve() if args.skill_root else _skill_root()
    svc = _svc(skill_root)
    asin = args.asin.strip().upper()
    site = _site_code(args.site)
    data_path = skill_root / "data" / f"reviews_{asin}_{site}.json"
    tasks = [t.to_dict() for t in svc.list_tasks(asin=asin, limit=20)]
    count = 0
    if data_path.exists():
        try:
            payload = json.loads(data_path.read_text(encoding="utf-8"))
            count = int(payload.get("count") or len(payload.get("reviews") or []))
        except Exception:
            count = 0
    print(
        json.dumps(
            {
                "ok": True,
                "asin": asin,
                "site": site,
                "resultExists": data_path.exists(),
                "count": count,
                "resultPath": str(data_path),
                "tasks": tasks,
                "skillRoot": str(skill_root),
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).resolve() if args.skill_root else _skill_root()
    svc = _svc(skill_root)
    if args.task_id:
        outcome = svc.run_task(args.task_id, channel=args.channel, headed=not args.headless)
    else:
        outcome = svc.run_next(channel=args.channel, headed=not args.headless)
        if outcome is None:
            print(json.dumps({"ok": True, "message": "queue empty"}, ensure_ascii=False))
            return 0
    print(
        json.dumps(
            {"ok": outcome.exit_code == 0, "exitCode": outcome.exit_code, "task": outcome.task.to_dict()},
            ensure_ascii=False,
        )
    )
    return int(outcome.exit_code)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="amazon-reviews-skill bridge for competitor analysis")
    parser.add_argument("--skill-root", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enq = sub.add_parser("enqueue")
    p_enq.add_argument("--asin", required=True)
    p_enq.add_argument("--site", default="US")
    p_enq.add_argument("--account", default="test-us-2")
    p_enq.add_argument("--target", type=int, default=300)
    p_enq.add_argument("--strategy", default="show_more")
    p_enq.add_argument("--pace", default="cautious")
    p_enq.add_argument("--max-pace", default="normal")
    p_enq.set_defaults(func=cmd_enqueue)

    p_task = sub.add_parser("task")
    p_task.add_argument("--id", required=True)
    p_task.set_defaults(func=cmd_task)

    p_st = sub.add_parser("status")
    p_st.add_argument("--asin", required=True)
    p_st.add_argument("--site", default="US")
    p_st.set_defaults(func=cmd_status)

    p_run = sub.add_parser("run")
    p_run.add_argument("--task-id", default=None)
    p_run.add_argument("--channel", default="chrome")
    p_run.add_argument("--headless", action="store_true")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
