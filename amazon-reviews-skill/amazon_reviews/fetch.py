"""Fetch up to N Amazon reviews via browser Show-more append + optional filter fallback.

Default engine is Playwright (real Chrome) because Amazon EdgeX blocks plain HTTP.
Primary path clicks ``a[data-hook=show-more-button]`` (nextPageToken append).
URL ``pageNumber`` is ignored by Amazon for many sessions — do not rely on it.
"""

from __future__ import annotations

import json
import random
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Protocol

from playwright.sync_api import sync_playwright

from .accounts import Account, AccountPool
from .browser import launch_persistent_context
from .crawl_log import CrawlLogger
from .http_client import ReviewHttpClient
from .pacer import HumanPacer
from .parser import Review, parse_reviews
from .sites import SiteConfig, get_site
from .softban import PageHealth, assess_review_page

STAR_FILTERS = [
    None,
    "five_star",
    "four_star",
    "three_star",
    "two_star",
    "one_star",
]
SORTS = ["recent", "helpful"]
MAX_PAGES_PER_COMBO = 10
DEFAULT_TARGET = 300
MAX_SHOW_MORE_CLICKS = 50
SHOW_MORE_SELECTOR = 'a[data-hook="show-more-button"]'
SHOW_MORE_SELECTORS = (
    'a[data-hook="show-more-button"]',
    '[data-hook="show-more-button"]',
    'span[data-hook="show-more-button"] a',
    "#cm_cr-pagination_bar li.a-last a",
)

SEED_KEYWORDS = [
    "quality",
    "size",
    "easy",
    "assembly",
    "sturdy",
    "cheap",
    "broken",
    "worth",
    "perfect",
    "small",
    "large",
    "color",
    "drawer",
    "charging",
    "usb",
    "led",
    "space",
    "solid",
    "flimsy",
    "love",
    "hate",
    "recommend",
    "return",
    "shipping",
    "package",
    "stable",
    "wobble",
    "height",
    "bedroom",
    "nightstand",
    "outlet",
    "cable",
    "light",
    "black",
    "white",
    "durable",
    "value",
    "money",
    "great",
    "good",
    "bad",
    "awful",
    "amazing",
]

STOPWORDS = {
    "this",
    "that",
    "with",
    "from",
    "have",
    "been",
    "were",
    "they",
    "them",
    "their",
    "what",
    "when",
    "where",
    "which",
    "while",
    "about",
    "would",
    "could",
    "should",
    "there",
    "these",
    "those",
    "into",
    "just",
    "like",
    "also",
    "very",
    "much",
    "more",
    "some",
    "only",
    "than",
    "then",
    "your",
    "you",
    "are",
    "was",
    "for",
    "and",
    "the",
    "but",
    "not",
    "all",
    "can",
    "had",
    "has",
    "its",
    "our",
    "out",
    "get",
    "got",
    "one",
    "two",
    "amazon",
    "review",
    "reviews",
    "stars",
    "star",
    "verified",
    "purchase",
    "purchased",
}

_READY_JS = """() => {
  const href = location.href || '';
  const text = (document.body && document.body.innerText) || '';
  if (href.includes('edgex/guard') || text.includes('Getting things ready')) return false;
  if (document.querySelector('[data-hook="review"]')) return true;
  if (text.includes('unusual activity') && text.includes('limit review access')) return true;
  if (document.querySelector('#ap_email') || document.querySelector('#ap_password')) return true;
  if (href.includes('/product-reviews/') && !href.includes('edgex')) return true;
  if (document.querySelector('#cm_cr-review_list')) return true;
  return false;
}"""

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\\-]{3,}")


@dataclass
class FetchCombo:
    sort_by: str
    filter_star: str | None = None
    keyword: str | None = None
    reviewer_type: str = "all_reviews"
    media_only: bool = False


@dataclass
class FetchResult:
    asin: str
    site: str
    account_id: str
    target: int
    engine: str = "browser"
    reviews: list[Review] = field(default_factory=list)
    pages_fetched: int = 0
    combos_tried: int = 0
    softbanned: bool = False
    needs_login: bool = False
    captcha: bool = False
    edgex_challenge: bool = False
    pagination_disabled: bool = False
    show_more_clicks: int = 0
    unique_review_ids: int = 0
    strategy: str = "show_more"
    stopped_reason: str = ""
    errors: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""

    @property
    def count(self) -> int:
        return len(self.reviews)

    def to_dict(self) -> dict[str, Any]:
        unique_ids = len({r.review_id for r in self.reviews if r.review_id})
        return {
            "asin": self.asin,
            "site": self.site,
            "account_id": self.account_id,
            "target": self.target,
            "engine": self.engine,
            "strategy": self.strategy,
            "count": self.count,
            "unique_review_ids": unique_ids,
            "pages_fetched": self.pages_fetched,
            "combos_tried": self.combos_tried,
            "show_more_clicks": self.show_more_clicks,
            "softbanned": self.softbanned,
            "needs_login": self.needs_login,
            "captcha": self.captcha,
            "edgex_challenge": self.edgex_challenge,
            "pagination_disabled": self.pagination_disabled,
            "stopped_reason": self.stopped_reason,
            "errors": self.errors,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "reviews": [r.to_dict() for r in self.reviews],
        }


class PageFetcher(Protocol):
    def get_html(self, url: str) -> str: ...

    def close(self) -> None: ...


class HttpPageFetcher:
    def __init__(self, site: SiteConfig, storage_path: Path) -> None:
        self.client = ReviewHttpClient(site, storage_path)

    def get_html(self, url: str) -> str:
        resp = self.client.get(url)
        return resp.text or ""

    def close(self) -> None:
        return None


class BrowserPageFetcher:
    """Fetch pages via a persistent Chrome profile + human-like dwell."""

    def __init__(
        self,
        site: SiteConfig,
        storage_path: Path,
        *,
        profile_dir: Path,
        channel: str = "chrome",
        headed: bool = True,
        ready_timeout_ms: int = 60_000,
        pacer: HumanPacer | None = None,
    ) -> None:
        self.site = site
        self.storage_path = Path(storage_path)
        self.profile_dir = Path(profile_dir)
        self.channel = channel
        self.headed = headed
        self.ready_timeout_ms = ready_timeout_ms
        self.pacer = pacer or HumanPacer()
        self.last_fetch_ms = 0.0
        self._pw = sync_playwright().start()
        self._context, used, self._chrome_proc = launch_persistent_context(
            self._pw,
            profile_dir=self.profile_dir,
            site_cfg=site,
            headed=headed,
            channel=channel,
        )
        self.used_channel = used
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self.warm_home()

    def warm_home(self, *, idle_s: float | None = None) -> None:
        try:
            self._page.goto(
                self.site.base_url + "/",
                wait_until="domcontentloaded",
                timeout=90_000,
            )
            self.pacer.dwell_on_page(self._page)
            if idle_s:
                self._page.wait_for_timeout(int(idle_s * 1000))
        except Exception:
            pass

    def get_html(self, url: str) -> str:
        import time as _time

        last_html = ""
        captcha_retried = False
        for attempt in range(3):
            t0 = _time.monotonic()
            self._page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            try:
                self._page.wait_for_function(_READY_JS, timeout=self.ready_timeout_ms)
            except Exception:
                self._page.wait_for_timeout(2000)
            self.pacer.dwell_on_page(self._page)
            last_html = self._page.content()
            health = assess_review_page(last_html)
            self.last_fetch_ms = (_time.monotonic() - t0) * 1000

            if health.captcha and not captcha_retried:
                # One long backoff + homepage warm, then single retry.
                captcha_retried = True
                self.pacer.captcha_backoff()
                self.warm_home(idle_s=random.uniform(3.0, 8.0))
                continue

            if health.edgex_challenge or health.needs_login:
                self.pacer.note_risk(health.reason or "challenge")
                self.warm_home(idle_s=2.0 + attempt * 2.0)
                continue
            break
        try:
            self._context.storage_state(path=str(self.storage_path))
        except Exception:
            pass
        return last_html

    def current_url(self) -> str:
        try:
            return self._page.url or ""
        except Exception:
            return ""

    def review_dom_count(self) -> int:
        try:
            return int(self._page.locator('[data-hook="review"]').count())
        except Exception:
            return 0

    def _locate_show_more(self):
        page = self._page
        for sel in SHOW_MORE_SELECTORS:
            loc = page.locator(sel)
            try:
                if loc.count() > 0 and loc.first.is_visible():
                    return loc.first
            except Exception:
                if loc.count() > 0:
                    return loc.first
        # Visible text (user-facing "Show 10 more reviews").
        for pattern in (
            re.compile(r"Show\s+\d+\s+more\s+reviews", re.I),
            re.compile(r"Show\s+more\s+reviews", re.I),
        ):
            for factory in (
                lambda p=pattern: page.get_by_role("link", name=p),
                lambda p=pattern: page.get_by_role("button", name=p),
                lambda p=pattern: page.get_by_text(p),
            ):
                try:
                    alt = factory()
                    if alt.count() > 0:
                        return alt.first
                except Exception:
                    continue
        return None

    def open_reviews_page(self, url: str) -> tuple[str, PageHealth]:
        """Navigate to a reviews listing URL (pageNumber is kept at 1)."""
        html = self.get_html(url)
        health = assess_review_page(html)
        if "/product-reviews/" not in self.current_url() and health.review_count_on_page == 0:
            health = PageHealth(
                ok=False,
                reason=f"redirected_off_reviews url={self.current_url()[:120]}",
            )
        return html, health

    def click_show_more_once(self) -> dict[str, Any]:
        """Click Show-more once and wait for appended reviews. Returns event dict."""
        before = self.review_dom_count()
        btn = self._locate_show_more()
        if btn is None:
            return {"ok": False, "reason": "no_show_more_button", "before": before, "after": before}
        try:
            btn.scroll_into_view_if_needed(timeout=5_000)
        except Exception:
            pass
        try:
            btn.click(timeout=10_000)
        except Exception:
            try:
                btn.click(timeout=10_000, force=True)
            except Exception as exc:
                return {
                    "ok": False,
                    "reason": f"click_failed: {exc}",
                    "before": before,
                    "after": before,
                }

        # Wait until DOM review count grows, button refreshes, or timeout.
        deadline = time.monotonic() + 25.0
        after = before
        while time.monotonic() < deadline:
            self._page.wait_for_timeout(400)
            href = self.current_url()
            if "/product-reviews/" not in href and "amazon." in href:
                return {
                    "ok": False,
                    "reason": "redirected_home_after_show_more",
                    "before": before,
                    "after": self.review_dom_count(),
                    "url": href[:160],
                }
            after = self.review_dom_count()
            if after > before:
                break
            html_probe = ""
            try:
                html_probe = self._page.content()
            except Exception:
                pass
            health = assess_review_page(html_probe) if html_probe else PageHealth(ok=True)
            if health.captcha or health.needs_login or health.softbanned or health.edgex_challenge:
                return {
                    "ok": False,
                    "reason": health.reason or "risk_after_show_more",
                    "before": before,
                    "after": after,
                    "health": health,
                }

        self.pacer.dwell_on_page(self._page)
        grown = after > before
        return {
            "ok": grown,
            "reason": "appended" if grown else "no_growth",
            "before": before,
            "after": after,
        }

    def close(self) -> None:
        try:
            self._context.storage_state(path=str(self.storage_path))
        except Exception:
            pass
        try:
            self._context.close()
        except Exception:
            pass
        if getattr(self, "_chrome_proc", None) is not None and self._chrome_proc.poll() is None:
            try:
                self._chrome_proc.terminate()
            except Exception:
                pass
        self._pw.stop()


def _base_combos() -> list[FetchCombo]:
    out: list[FetchCombo] = []
    for sort_by in SORTS:
        out.append(FetchCombo(sort_by=sort_by))
    for star in STAR_FILTERS[1:]:
        for sort_by in SORTS:
            out.append(FetchCombo(sort_by=sort_by, filter_star=star))
    # Verified-only and media-only as light extras.
    out.append(FetchCombo(sort_by="recent", reviewer_type="avp_only_reviews"))
    out.append(FetchCombo(sort_by="helpful", reviewer_type="avp_only_reviews"))
    out.append(FetchCombo(sort_by="recent", media_only=True))
    out.append(FetchCombo(sort_by="helpful", media_only=True))
    return out


def _mine_keywords(reviews: list[Review], *, limit: int = 40) -> list[str]:
    counts: Counter[str] = Counter()
    used_in_urls: set[str] = set()
    for rev in reviews:
        blob = f"{rev.title} {rev.body}"
        for word in _WORD_RE.findall(blob):
            w = word.lower().strip("-'")
            if len(w) < 4 or w in STOPWORDS:
                continue
            counts[w] += 1
        src = rev.source_url or ""
        m = re.search(r"filterByKeyword=([^&]+)", src)
        if m:
            from urllib.parse import unquote_plus

            used_in_urls.add(unquote_plus(m.group(1)).lower())
    mined = [w for w, _ in counts.most_common(limit * 2)]
    # Prefer mined terms (fresh unlocks) before generic seeds; skip already-used keywords.
    ordered: list[str] = []
    seen: set[str] = set()
    for w in mined + SEED_KEYWORDS:
        wl = w.lower()
        if wl in seen or wl in used_in_urls:
            continue
        seen.add(wl)
        ordered.append(wl)
    return ordered[:limit]


def _keyword_combos(keywords: Iterable[str], *, deep: bool = False) -> list[FetchCombo]:
    """Prefer light keyword×sort first; star×keyword only in deep mode (higher risk)."""
    out: list[FetchCombo] = []
    for kw in keywords:
        for sort_by in SORTS:
            out.append(FetchCombo(sort_by=sort_by, keyword=kw))
        if deep:
            for star in ("one_star", "five_star", "three_star"):
                out.append(FetchCombo(sort_by="recent", filter_star=star, keyword=kw))
    return out


def _apply_health(
    result: FetchResult,
    health: PageHealth,
    pool: AccountPool,
    account: Account,
    *,
    mark_pool: bool = True,
) -> bool:
    if health.softbanned:
        result.softbanned = True
        result.stopped_reason = health.reason
        if mark_pool:
            pool.mark_softbanned(account, health.reason)
        return True
    if health.needs_login:
        result.needs_login = True
        result.stopped_reason = health.reason
        if mark_pool:
            pool.mark_expired(account, health.reason)
        return True
    if health.captcha:
        result.captcha = True
        result.stopped_reason = health.reason
        return True
    if health.edgex_challenge:
        result.edgex_challenge = True
        result.stopped_reason = health.reason
        return True
    return False


def fetch_reviews(
    asin: str,
    *,
    site: str = "com",
    pool: AccountPool,
    account_id: str | None = None,
    target: int = DEFAULT_TARGET,
    page_delay: tuple[float, float] | None = None,
    max_pages_per_combo: int = MAX_PAGES_PER_COMBO,
    soft_degradation_pages: int = 2,
    engine: str = "browser",
    channel: str = "chrome",
    headed: bool = True,
    max_keywords: int = 40,
    resume_from: Path | None = None,
    pace_mode: str | None = None,
    max_pace: str = "normal",
    log_dir: Path | None = None,
    strategy: str = "show_more",
    checkpoint_path: Path | None = None,
    max_show_more_clicks: int = MAX_SHOW_MORE_CLICKS,
) -> FetchResult:
    asin = asin.strip().upper()
    site_cfg: SiteConfig = get_site(site)
    account: Account = pool.pick(site_cfg.code, account_id=account_id)
    if account.status in {"needs_login", "expired"}:
        raise RuntimeError(
            f"账号 {account.id} 状态={account.status}，请先执行: "
            f"python -m amazon_reviews.cli login --account {account.id} --site {site_cfg.code}"
        )
    storage = account.storage_path(pool.root)
    profile = account.profile_path(pool.root, site_cfg.code)
    account.profile_dir = str(profile)
    try:
        account.storage_state = str(storage.relative_to(pool.root)).replace("\\", "/")
    except ValueError:
        account.storage_state = str(storage)
    pool.save()

    root = pool.root
    logger = CrawlLogger(
        asin=asin,
        site=site_cfg.code,
        account_id=account.id,
        log_dir=Path(log_dir) if log_dir else root / "logs",
    )

    pacer = HumanPacer(
        force_mode=pace_mode or "cautious",
        max_mode=max_pace,
        on_event=logger.pace_event,
    )
    if page_delay is not None:
        from . import pacer as pacer_mod

        pacer_mod.PAGE_DELAYS[pacer.mode] = page_delay

    result = FetchResult(
        asin=asin,
        site=site_cfg.code,
        account_id=account.id,
        target=target,
        engine=engine,
        strategy=strategy,
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    seen: set[str] = set()
    if resume_from and Path(resume_from).exists():
        prev = json.loads(Path(resume_from).read_text(encoding="utf-8"))
        for item in prev.get("reviews", []):
            rid = item.get("review_id")
            if not rid or rid in seen:
                continue
            seen.add(rid)
            result.reviews.append(
                Review(
                    review_id=rid,
                    asin=item.get("asin") or asin,
                    site=item.get("site") or site_cfg.code,
                    title=item.get("title") or "",
                    body=item.get("body") or "",
                    rating=item.get("rating"),
                    date_text=item.get("date_text") or "",
                    author=item.get("author") or "",
                    verified=bool(item.get("verified")),
                    helpful_votes=item.get("helpful_votes"),
                    variant=item.get("variant") or "",
                    source_url=item.get("source_url") or "",
                    filter_star=item.get("filter_star"),
                    sort_by=item.get("sort_by") or "",
                )
            )
        print(f"resume: loaded {len(seen)} reviews from {resume_from}", flush=True)
    logger.reviews_start = len(seen)

    if engine == "http":
        fetcher: PageFetcher = HttpPageFetcher(site_cfg, storage)
    elif engine == "browser":
        print(f"using persistent profile: {profile}", flush=True)
        fetcher = BrowserPageFetcher(
            site_cfg,
            storage,
            profile_dir=profile,
            channel=channel,
            headed=headed,
            pacer=pacer,
        )
    else:
        raise ValueError(f"Unknown engine: {engine}")

    pool.mark_used(account)
    degradation_hits = 0
    pagination_dup_hits = 0
    last_keyword: str | None = None
    # Amazon ignores URL pageNumber for many sessions; never walk page>1.
    max_pages_per_combo = 1

    def checkpoint() -> None:
        if not checkpoint_path:
            return
        result.unique_review_ids = len(seen)
        try:
            save_result(result, Path(checkpoint_path))
            logger.log("checkpoint", total=len(seen), path=str(checkpoint_path))
        except Exception as exc:  # noqa: BLE001
            logger.log("checkpoint_error", error=str(exc))

    def merge_html(
        html: str,
        *,
        url: str,
        sort_by: str,
        filter_star: str | None = None,
    ) -> int:
        new_on_page = 0
        for rev in parse_reviews(
            html,
            asin=asin,
            site=site_cfg.code,
            source_url=url,
            sort_by=sort_by,
            filter_star=filter_star,
        ):
            if not rev.review_id or rev.review_id in seen:
                continue
            seen.add(rev.review_id)
            result.reviews.append(rev)
            new_on_page += 1
            if len(seen) >= target:
                break
        return new_on_page

    def maybe_session_cooldown() -> None:
        if not isinstance(fetcher, BrowserPageFetcher):
            return
        if not pacer.needs_session_cooldown():
            return
        from .pacer import SESSION_COOLDOWN_EVERY

        _, (lo, hi) = SESSION_COOLDOWN_EVERY[pacer.mode]
        idle = random.uniform(lo, hi)
        logger.log("session_cooldown_start", idle_s=round(idle, 2), mode=pacer.mode)
        fetcher.warm_home(idle_s=idle)
        pacer.mark_session_cooldown_done(idle)

    def run_show_more_pass(combo: FetchCombo) -> bool:
        """Open listing once, click Show-more until target / no button. True=abort fetch."""
        if len(seen) >= target:
            result.stopped_reason = f"reached_target_{target}"
            return True
        if not isinstance(fetcher, BrowserPageFetcher):
            result.errors.append("show_more requires browser engine")
            return True

        result.combos_tried += 1
        logger.combos_tried = result.combos_tried
        url = site_cfg.reviews_url(
            asin,
            page=1,
            sort_by=combo.sort_by,
            filter_by_star=combo.filter_star,
            reviewer_type=combo.reviewer_type,
            keyword=combo.keyword,
            media_only=combo.media_only,
        )
        logger.log(
            "show_more_start",
            sort_by=combo.sort_by,
            filter_star=combo.filter_star,
            keyword=combo.keyword,
            url=url[:180],
        )
        pacer.wait_between_combos()

        try:
            html, health = fetcher.open_reviews_page(url)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{url}: {exc}")
            pacer.note_risk(str(exc))
            logger.log("page_error", error=str(exc), url=url[:180])
            return False

        result.pages_fetched += 1
        if _apply_health(result, health, pool, account):
            merge_html(html, url=url, sort_by=combo.sort_by, filter_star=combo.filter_star)
            checkpoint()
            logger.log("stop_health", reason=health.reason, total_reviews=len(seen))
            return True

        new_n = merge_html(html, url=url, sort_by=combo.sort_by, filter_star=combo.filter_star)
        logger.note_page(
            duration_ms=getattr(fetcher, "last_fetch_ms", 0.0),
            new_reviews=new_n,
            total_reviews=len(seen),
            pace_mode=pacer.mode,
            url=url,
            health=health.reason or "ok",
        )
        if new_n:
            logger.log("progress", total=len(seen), target=target, keyword=combo.keyword)
            checkpoint()
        pacer.note_ok(got_new=new_n > 0)

        if len(seen) >= target:
            result.stopped_reason = f"reached_target_{target}"
            return True

        no_grow_streak = 0
        for click_i in range(1, max_show_more_clicks + 1):
            if len(seen) >= target:
                result.stopped_reason = f"reached_target_{target}"
                return True

            # Stay on the reviews page; do not warm homepage between Show-more clicks.
            pacer.wait_after_page()
            event = fetcher.click_show_more_once()
            result.show_more_clicks += 1
            logger.log(
                "show_more_click",
                click=click_i,
                ok=event.get("ok"),
                reason=event.get("reason"),
                before=event.get("before"),
                after=event.get("after"),
                total_reviews=len(seen),
            )

            health_obj = event.get("health")
            if isinstance(health_obj, PageHealth) and _apply_health(
                result, health_obj, pool, account
            ):
                try:
                    html = fetcher._page.content()
                    merge_html(html, url=url, sort_by=combo.sort_by, filter_star=combo.filter_star)
                except Exception:
                    pass
                checkpoint()
                return True

            reason = str(event.get("reason") or "")
            if reason in {"redirected_home_after_show_more", "no_show_more_button"}:
                result.pagination_disabled = reason == "no_show_more_button"
                logger.log("show_more_stop", reason=reason, total_reviews=len(seen))
                break
            if not event.get("ok"):
                no_grow_streak += 1
                if no_grow_streak >= 2:
                    logger.log("show_more_stop", reason="no_growth_streak", total_reviews=len(seen))
                    break
                continue

            no_grow_streak = 0
            try:
                html = fetcher._page.content()
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"show_more content: {exc}")
                break

            health = assess_review_page(html)
            if _apply_health(result, health, pool, account):
                merge_html(html, url=url, sort_by=combo.sort_by, filter_star=combo.filter_star)
                checkpoint()
                return True

            new_n = merge_html(html, url=url, sort_by=combo.sort_by, filter_star=combo.filter_star)
            pacer.note_ok(got_new=new_n > 0)
            logger.log(
                "progress",
                total=len(seen),
                target=target,
                keyword=combo.keyword,
                new_reviews=new_n,
                show_more_click=click_i,
            )
            if new_n:
                checkpoint()
            else:
                no_grow_streak += 1
                if no_grow_streak >= 2:
                    break

        return bool(
            result.softbanned or result.needs_login or result.captcha or result.edgex_challenge
        )

    def run_combo(combo: FetchCombo) -> bool:
        """Legacy single-page filter slice (no pageNumber walk). True=abort."""
        nonlocal degradation_hits, pagination_dup_hits, last_keyword
        if len(seen) >= target:
            result.stopped_reason = f"reached_target_{target}"
            return True

        result.combos_tried += 1
        logger.combos_tried = result.combos_tried
        logger.log(
            "combo_start",
            sort_by=combo.sort_by,
            filter_star=combo.filter_star,
            keyword=combo.keyword,
            reviewer_type=combo.reviewer_type,
            media_only=combo.media_only,
        )

        if combo.keyword and combo.keyword != last_keyword:
            if last_keyword is not None and isinstance(fetcher, BrowserPageFetcher):
                pause = random.uniform(12.0, 25.0)
                logger.log(
                    "keyword_switch",
                    from_kw=last_keyword,
                    to_kw=combo.keyword,
                    pause_s=round(pause, 2),
                )
                fetcher.warm_home(idle_s=pause)
            last_keyword = combo.keyword

        pacer.wait_between_combos()
        maybe_session_cooldown()

        url = site_cfg.reviews_url(
            asin,
            page=1,
            sort_by=combo.sort_by,
            filter_by_star=combo.filter_star,
            reviewer_type=combo.reviewer_type,
            keyword=combo.keyword,
            media_only=combo.media_only,
        )
        try:
            html = fetcher.get_html(url)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{url}: {exc}")
            pacer.note_risk(str(exc))
            logger.log("page_error", error=str(exc), url=url[:180])
            return False

        result.pages_fetched += 1
        duration_ms = getattr(fetcher, "last_fetch_ms", 0.0)
        health = assess_review_page(html)
        result.pagination_disabled = True

        if _apply_health(result, health, pool, account):
            merge_html(html, url=url, sort_by=combo.sort_by, filter_star=combo.filter_star)
            checkpoint()
            logger.log("stop_health", reason=health.reason, total_reviews=len(seen))
            return True

        new_on_page = merge_html(
            html, url=url, sort_by=combo.sort_by, filter_star=combo.filter_star
        )
        logger.note_page(
            duration_ms=duration_ms,
            new_reviews=new_on_page,
            total_reviews=len(seen),
            pace_mode=pacer.mode,
            url=url,
            health=health.reason or "ok",
        )
        if new_on_page:
            logger.log("progress", total=len(seen), target=target, keyword=combo.keyword)
            checkpoint()
        pacer.note_ok(got_new=new_on_page > 0)
        pacer.wait_after_page()
        return False

    try:
        use_show_more = strategy in {"show_more", "hybrid"} and engine == "browser"
        use_matrix = strategy in {"matrix", "hybrid"}

        if use_show_more:
            print(
                f"strategy={strategy}: Show-more primary "
                f"(NO pageNumber walk; click '{SHOW_MORE_SELECTOR}' / text fallback, "
                f"max_clicks={max_show_more_clicks}/pass)",
                flush=True,
            )
            show_passes: list[FetchCombo] = [
                FetchCombo(sort_by="recent"),
                FetchCombo(sort_by="helpful"),
            ]
            for star in STAR_FILTERS[1:]:
                show_passes.append(FetchCombo(sort_by="recent", filter_star=star))
            for combo in show_passes:
                if run_show_more_pass(combo):
                    break
                if len(seen) >= target:
                    break
                if isinstance(fetcher, BrowserPageFetcher):
                    pause = random.uniform(6.0, 12.0)
                    logger.log("pass_switch_pause", pause_s=round(pause, 2))
                    fetcher._page.wait_for_timeout(int(pause * 1000))

        if (
            use_matrix
            and len(seen) < target
            and not (
                result.softbanned or result.needs_login or result.captcha or result.edgex_challenge
            )
        ):
            print(
                f"strategy matrix fill from {len(seen)} "
                f"(filter slices only; pageNumber disabled)",
                flush=True,
            )
            if len(seen) < 30:
                for combo in _base_combos():
                    if run_combo(combo):
                        break
            keywords = _mine_keywords(result.reviews, limit=max_keywords)
            if keywords and len(seen) < target and not (
                result.softbanned or result.needs_login or result.captcha or result.edgex_challenge
            ):
                print(
                    f"keyword phase(light): {len(keywords)} keywords -> {keywords[:12]}",
                    flush=True,
                )
                stagnant = 0
                for combo in _keyword_combos(keywords, deep=False):
                    before = len(seen)
                    if run_combo(combo):
                        break
                    if len(seen) == before:
                        stagnant += 1
                    else:
                        stagnant = 0
                    if stagnant >= 24 and len(seen) > 0:
                        break

        if not result.stopped_reason:
            if len(seen) >= target:
                result.stopped_reason = f"reached_target_{target}"
            else:
                result.stopped_reason = (
                    "show_more_exhausted" if use_show_more else "matrix_exhausted"
                )
        result.unique_review_ids = len(seen)
        checkpoint()
    finally:
        result.finished_at = datetime.now(timezone.utc).isoformat()
        fetcher.close()
        logger.reviews_end = len(seen)
        logger.pages_fetched = result.pages_fetched
        logger.finish(result=result.to_dict())

    return result



def save_result(result: FetchResult, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
