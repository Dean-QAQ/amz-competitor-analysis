"""CLI: login | fetch | sites | pool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from amazon_reviews.accounts import AccountPool
from amazon_reviews.api import ReviewsService
from amazon_reviews.auth_playwright import login_and_save, refresh_storage_via_goto
from amazon_reviews.fetch import fetch_reviews, save_result
from amazon_reviews.sites import list_site_codes


def _default_pool_path() -> Path:
    return ROOT / "accounts" / "pool.json"


def _service(pool: Path | None = None) -> ReviewsService:
    return ReviewsService(ROOT, pool_path=pool or _default_pool_path())


def _load_pool(path: Path | None) -> AccountPool:
    pool_path = path or _default_pool_path()
    if not pool_path.exists():
        example = ROOT / "accounts" / "pool.example.json"
        raise SystemExit(
            f"缺少账号池: {pool_path}\n请复制: copy accounts\\pool.example.json accounts\\pool.json\n模板: {example}"
        )
    return AccountPool.load(pool_path, root=ROOT)


def cmd_sites(_: argparse.Namespace) -> int:
    print("\n".join(list_site_codes()))
    return 0


def cmd_pool(args: argparse.Namespace) -> int:
    pool = _load_pool(Path(args.pool) if args.pool else None)
    print(json.dumps(pool.as_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_login(args: argparse.Namespace) -> int:
    pool = _load_pool(Path(args.pool) if args.pool else None)
    account = pool.get(args.account)
    if args.site not in account.sites and "*" not in account.sites:
        account.sites.append(args.site)
    storage = account.storage_path(pool.root)
    profile = account.profile_path(pool.root, args.site)
    common = dict(
        site=args.site,
        storage_path=storage,
        profile_dir=profile,
        headed=not args.headless,
        channel=args.channel,
        account_id=account.id,
        root=pool.root,
    )
    if args.refresh:
        refresh_storage_via_goto(**common)
    else:
        login_and_save(**common, auto_wait=not args.no_auto_wait)
    account.storage_state = str(storage.relative_to(ROOT)).replace("\\", "/")
    try:
        account.profile_dir = str(profile.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        account.profile_dir = str(profile)
    account.status = "healthy"
    account.last_error = ""
    pool.save()
    # Re-queue tasks waiting on this account after manual CLI login.
    try:
        svc = _service(Path(args.pool) if args.pool else None)
        for task in svc.tasks.list(status="needs_login", limit=500):
            if task.site == args.site and (
                not task.account_id or task.account_id == account.id
            ):
                svc.tasks.transition(task, "queued", error="")
    except Exception:
        pass
    print(f"账号 {account.id} 已绑定 profile -> {account.profile_dir}")
    print(f"账号 {account.id} 已绑定 storage_state -> {account.storage_state}")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    pool = _load_pool(Path(args.pool) if args.pool else None)
    default_out = ROOT / "data" / f"reviews_{args.asin}_{args.site}.json"
    out = Path(args.out) if args.out else default_out
    resume = None
    if args.resume:
        resume = Path(args.resume) if args.resume != "auto" else out

    page_delay = None
    if args.delay_min is not None or args.delay_max is not None:
        page_delay = (
            args.delay_min if args.delay_min is not None else 4.5,
            args.delay_max if args.delay_max is not None else 8.5,
        )

    result = fetch_reviews(
        args.asin,
        site=args.site,
        pool=pool,
        account_id=args.account,
        target=args.target,
        page_delay=page_delay,
        engine=args.engine,
        channel=args.channel,
        headed=not args.headless,
        resume_from=resume,
        pace_mode=args.pace,
        max_pace=args.max_pace,
        log_dir=Path(args.log_dir) if args.log_dir else ROOT / "logs",
        strategy=args.strategy,
        checkpoint_path=out,
        max_show_more_clicks=args.max_show_more_clicks,
    )
    save_result(result, out)
    summary = {
        "asin": result.asin,
        "site": result.site,
        "account_id": result.account_id,
        "engine": result.engine,
        "strategy": result.strategy,
        "count": result.count,
        "unique_review_ids": result.unique_review_ids or len({r.review_id for r in result.reviews}),
        "show_more_clicks": result.show_more_clicks,
        "target": result.target,
        "pages_fetched": result.pages_fetched,
        "combos_tried": result.combos_tried,
        "softbanned": result.softbanned,
        "needs_login": result.needs_login,
        "captcha": result.captcha,
        "edgex_challenge": result.edgex_challenge,
        "pagination_disabled": result.pagination_disabled,
        "stopped_reason": result.stopped_reason,
        "out": str(out),
        "logs": str(ROOT / "logs"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if result.captcha:
        print(
            "\n触发验证码已停止（登录态通常仍在）。可稍后 --resume；"
            "建议保持 --max-pace normal 或 cautious。\n"
        )
    if result.needs_login:
        print(
            "\n会话需要重新登录。请执行:\n"
            f"  python -m amazon_reviews.cli login --account {result.account_id} --site {result.site}\n"
            "然后:\n"
            f"  python -m amazon_reviews.cli fetch --asin {result.asin} --site {result.site} "
            f"--account {result.account_id} --resume\n"
        )
    if result.softbanned or result.needs_login or result.captcha or result.edgex_challenge:
        return 2
    return 0


def cmd_enqueue(args: argparse.Namespace) -> int:
    svc = _service(Path(args.pool) if args.pool else None)
    task = svc.enqueue(
        args.asin,
        site=args.site,
        account_id=args.account,
        target=args.target,
        strategy=args.strategy,
        pace=args.pace,
        max_pace=args.max_pace,
        max_show_more_clicks=args.max_show_more_clicks,
        meta={"source": "cli"},
    )
    print(json.dumps(task.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_tasks(args: argparse.Namespace) -> int:
    svc = _service(Path(args.pool) if args.pool else None)
    rows = svc.list_tasks(status=args.status, asin=args.asin, limit=args.limit)
    print(json.dumps([t.to_dict() for t in rows], ensure_ascii=False, indent=2))
    return 0


def cmd_task(args: argparse.Namespace) -> int:
    svc = _service(Path(args.pool) if args.pool else None)
    print(json.dumps(svc.task_snapshot(args.id), ensure_ascii=False, indent=2))
    return 0


def cmd_worker(args: argparse.Namespace) -> int:
    svc = _service(Path(args.pool) if args.pool else None)
    if args.task_id:
        outcome = svc.run_task(
            args.task_id,
            channel=args.channel,
            headed=not args.headless,
            resume=not args.no_resume,
        )
    else:
        outcome = svc.run_next(
            channel=args.channel,
            headed=not args.headless,
            resume=not args.no_resume,
        )
        if outcome is None:
            print(json.dumps({"ok": True, "message": "queue empty"}, ensure_ascii=False))
            return 0
    print(json.dumps(outcome.task.to_dict(), ensure_ascii=False, indent=2))
    return int(outcome.exit_code)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="amazon-reviews",
        description="Amazon 评论拉取：持久 Chrome 配置 + 仿真人限速（宽松时自动加快）",
    )
    parser.add_argument("--pool", default=None, help="账号池 JSON，默认 accounts/pool.json")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sites = sub.add_parser("sites", help="列出支持的站点 code")
    p_sites.set_defaults(func=cmd_sites)

    p_pool = sub.add_parser("pool", help="打印账号池")
    p_pool.set_defaults(func=cmd_pool)

    p_login = sub.add_parser("login", help="用持久 Chrome 配置登录并保存")
    p_login.add_argument("--account", required=True, help="账号 id，如 test-us-2")
    p_login.add_argument("--site", default="com", help="站点 code，默认 com")
    p_login.add_argument("--refresh", action="store_true", help="在已有配置上刷新登录")
    p_login.add_argument("--headless", action="store_true", help="无头（不推荐登录）")
    p_login.add_argument(
        "--channel",
        default="chrome",
        help="浏览器通道：chrome（默认）/ msedge",
    )
    p_login.add_argument(
        "--no-auto-wait",
        action="store_true",
        help="关闭自动检测登录；改为终端按 Enter 保存",
    )
    p_login.set_defaults(func=cmd_login)

    p_fetch = sub.add_parser("fetch", help="按 ASIN 拉取评论")
    p_fetch.add_argument("--asin", required=True)
    p_fetch.add_argument("--site", default="com")
    p_fetch.add_argument("--account", default=None, help="指定账号；默认选健康账号")
    p_fetch.add_argument("--target", type=int, default=300)
    p_fetch.add_argument(
        "--delay-min",
        type=float,
        default=None,
        help="可选：覆盖当前 pace 档位的最小页间隔（秒）",
    )
    p_fetch.add_argument(
        "--delay-max",
        type=float,
        default=None,
        help="可选：覆盖当前 pace 档位的最大页间隔（秒）",
    )
    p_fetch.add_argument(
        "--pace",
        default="cautious",
        choices=["cautious", "normal", "relaxed"],
        help="初始限速档（默认 cautious）",
    )
    p_fetch.add_argument(
        "--max-pace",
        default="normal",
        choices=["cautious", "normal", "relaxed"],
        help="最高限速档（默认 normal，避免过快触发验证码；需更快可设 relaxed）",
    )
    p_fetch.add_argument(
        "--log-dir",
        default=None,
        help="日志目录，默认 logs/（jsonl + summary）",
    )
    p_fetch.add_argument(
        "--engine",
        default="browser",
        choices=["browser", "http"],
        help="默认 browser（持久 Chrome）；http 易卡 EdgeX",
    )
    p_fetch.add_argument("--channel", default="chrome", help="browser 通道：chrome/msedge")
    p_fetch.add_argument("--headless", action="store_true", help="无头（更容易触发风控）")
    p_fetch.add_argument(
        "--resume",
        nargs="?",
        const="auto",
        default=None,
        help="从已有 JSON 续跑；写 --resume 默认续当前输出文件",
    )
    p_fetch.add_argument(
        "--strategy",
        default="show_more",
        choices=["show_more", "hybrid", "matrix"],
        help="默认 show_more：点 Show 10 more 追加；hybrid=不够再筛过滤片；matrix=旧筛选矩阵",
    )
    p_fetch.add_argument(
        "--max-show-more-clicks",
        type=int,
        default=50,
        help="每个排序/星级 pass 最多点几次 Show more（默认 50）",
    )
    p_fetch.add_argument("--out", default=None, help="输出 JSON 路径（同时作 checkpoint）")
    p_fetch.set_defaults(func=cmd_fetch)

    p_enq = sub.add_parser("enqueue", help="入队一个 ASIN 抓取任务（不立刻跑）")
    p_enq.add_argument("--asin", required=True)
    p_enq.add_argument("--site", default="com")
    p_enq.add_argument("--account", default=None)
    p_enq.add_argument("--target", type=int, default=300)
    p_enq.add_argument(
        "--strategy",
        default="show_more",
        choices=["show_more", "hybrid", "matrix"],
    )
    p_enq.add_argument("--pace", default="cautious", choices=["cautious", "normal", "relaxed"])
    p_enq.add_argument("--max-pace", default="normal", choices=["cautious", "normal", "relaxed"])
    p_enq.add_argument("--max-show-more-clicks", type=int, default=50)
    p_enq.set_defaults(func=cmd_enqueue)

    p_tasks = sub.add_parser("tasks", help="列出任务队列")
    p_tasks.add_argument("--status", default=None, help="过滤状态 queued/running/done/...")
    p_tasks.add_argument("--asin", default=None)
    p_tasks.add_argument("--limit", type=int, default=50)
    p_tasks.set_defaults(func=cmd_tasks)

    p_task = sub.add_parser("task", help="查看单个任务快照")
    p_task.add_argument("--id", required=True, help="任务 id")
    p_task.set_defaults(func=cmd_task)

    p_worker = sub.add_parser("worker", help="执行队列中下一个任务，或指定 --task-id")
    p_worker.add_argument("--task-id", default=None, help="指定任务；默认 claim 最早 queued")
    p_worker.add_argument("--channel", default="chrome")
    p_worker.add_argument("--headless", action="store_true")
    p_worker.add_argument(
        "--no-resume",
        action="store_true",
        help="忽略已有 reviews JSON，从头抓",
    )
    p_worker.set_defaults(func=cmd_worker)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
