"""Playwright login helper using a real Chrome profile via CDP."""

from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from .browser import launch_persistent_context, profile_dir_for
from .sites import SiteConfig, get_site

_SIGNED_IN_JS = """() => {
  const line = document.querySelector('#nav-link-accountList-nav-line-1, #nav-link-accountList .nav-line-1');
  const text = ((line && line.textContent) || '').trim().toLowerCase();
  // Require visible Hello greeting — do NOT trust at-main cookie alone.
  if (text && text.includes('hello') && !text.includes('sign in')) return true;
  if (document.querySelector('#nav-item-signout, #nav-item-signout-mobile')) return true;
  return false;
}"""


def _wait_signed_in(page, *, timeout_ms: int) -> bool:
    waited = 0
    step = 2_000
    while waited < timeout_ms:
        try:
            if page.evaluate(_SIGNED_IN_JS):
                return True
        except Exception:
            pass
        page.wait_for_timeout(step)
        waited += step
        if waited % 10_000 == 0:
            print(f"仍在等待登录… ({waited // 1000}s / {timeout_ms // 1000}s)", flush=True)
    try:
        return bool(page.evaluate(_SIGNED_IN_JS))
    except Exception:
        return False


def login_and_save(
    *,
    site: str | SiteConfig = "com",
    storage_path: Path,
    profile_dir: Path | None = None,
    headed: bool = True,
    timeout_ms: int = 600_000,
    channel: str | None = None,
    auto_wait: bool = True,
    account_id: str = "account",
    root: Path | None = None,
) -> Path:
    """Open real Chrome with durable profile; user logs in; save storage_state backup."""
    site_cfg = site if isinstance(site, SiteConfig) else get_site(site)
    storage_path = Path(storage_path)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    root = root or storage_path.parent.parent.parent
    profile = Path(profile_dir) if profile_dir else profile_dir_for(account_id, root, site_cfg.code)

    with sync_playwright() as p:
        context, used, proc = launch_persistent_context(
            p,
            profile_dir=profile,
            site_cfg=site_cfg,
            headed=headed,
            channel=channel or "chrome",
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto(site_cfg.base_url + "/", wait_until="domcontentloaded", timeout=90_000)
        except Exception as exc:
            print(f"首页加载告警: {exc}", flush=True)
        page.wait_for_timeout(2_500)
        try:
            body_len = page.evaluate("() => document.body ? document.body.innerText.length : 0")
        except Exception:
            body_len = 0
        print(f"browser={used} profile={profile} body_text_len={body_len}", flush=True)
        if body_len < 40:
            print(
                "若仍白屏：在打开的窗口地址栏手动回车刷新 amazon.com；"
                "或关掉所有 Chrome 后重试。",
                flush=True,
            )

        try:
            page.click("#nav-link-accountList", timeout=5_000)
            page.wait_for_timeout(1_500)
        except Exception:
            pass

        print(f"请在打开的 Chrome（持久配置）里登录 Amazon ({site_cfg.host})。", flush=True)
        if auto_wait:
            print(f"检测到已登录后会自动保存（最长 {timeout_ms // 1000}s）。", flush=True)
            signed_in = _wait_signed_in(page, timeout_ms=timeout_ms)
            if signed_in:
                print("已检测到登录态，正在验证评论页访问…", flush=True)
                try:
                    page.goto(
                        site_cfg.base_url + "/product-reviews/B0DB142C6Y/?sortBy=recent",
                        wait_until="domcontentloaded",
                        timeout=60_000,
                    )
                    page.wait_for_timeout(2500)
                    html = page.content()
                    if 'id="ap_email"' in html or 'name="email"' in html and "signIn" in html:
                        print("警告：评论页仍要求登录，请在窗口内完成登录/验证后再等检测。", flush=True)
                        signed_in = _wait_signed_in(page, timeout_ms=min(timeout_ms, 300_000))
                except Exception as exc:
                    print(f"评论页验证告警: {exc}", flush=True)
                print("正在保存…", flush=True)
            else:
                print("未稳定检测到登录态，仍保存当前配置（请确认右上角为 Hello）。", flush=True)
        else:
            print("登录完成后回到终端按 Enter 保存…", flush=True)
            try:
                input()
            except EOFError:
                _wait_signed_in(page, timeout_ms=min(timeout_ms, 120_000))

        # Keep Chrome open briefly so profile cookies flush to disk.
        try:
            page.goto(site_cfg.base_url + "/", wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(2_000)
        except Exception:
            pass
        try:
            context.storage_state(path=str(storage_path))
        except Exception as exc:
            print(f"storage_state 备份失败（配置仍可用）: {exc}", flush=True)

        # Disconnect CDP but leave Chrome process running so profile settles;
        # fetch will reuse/start cleanly.
        try:
            # Playwright CDP: closing browser connection without killing chrome.
            browser = context.browser
            if browser:
                browser.close()
        except Exception:
            pass
        # Do not terminate proc immediately — give Chrome a moment, then close.
        if proc is not None and proc.poll() is None:
            page_wait = 3
            time.sleep(page_wait)
            try:
                proc.terminate()
            except Exception:
                pass

    print(f"已保存登录态: profile={profile} storage={storage_path}", flush=True)
    return storage_path


def refresh_storage_via_goto(
    *,
    site: str | SiteConfig,
    storage_path: Path,
    profile_dir: Path | None = None,
    headed: bool = True,
    channel: str | None = None,
    account_id: str = "account",
    root: Path | None = None,
) -> Path:
    return login_and_save(
        site=site,
        storage_path=storage_path,
        profile_dir=profile_dir,
        headed=headed,
        channel=channel,
        account_id=account_id,
        root=root,
        auto_wait=True,
        timeout_ms=300_000,
    )
