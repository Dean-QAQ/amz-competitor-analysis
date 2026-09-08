"""Shared Playwright browser launch helpers.

Prefer: start real Chrome with --remote-debugging-port, then CDP attach.
Profile dirs use an ASCII home path to avoid Chrome ignoring non-ASCII user-data-dir.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, Playwright

from .sites import SiteConfig

PREFERRED_CHANNELS = ("chrome", "msedge")
DEFAULT_CDP_PORT = 9333

# Chrome on Windows often ignores --user-data-dir when the path contains non-ASCII.
# Keep durable profiles under the user home ASCII path.
ASCII_PROFILE_ROOT = Path.home() / ".amazon-reviews-profiles"

_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
"""

_CHROME_CANDIDATES = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
]
_EDGE_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def profile_dir_for(account_id: str, root: Path | None = None, site: str = "com") -> Path:
    """Return ASCII-safe durable profile directory."""
    _ = root  # kept for call-site compatibility
    path = ASCII_PROFILE_ROOT / f"{account_id}.{site}"
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def _safe_print(msg: str) -> None:
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(msg.encode(enc, errors="replace").decode(enc, errors="replace"), flush=True)


def _find_browser_exe(channel: str | None = "chrome") -> Path:
    channel = (channel or "chrome").lower()
    if channel == "msedge":
        candidates = list(_EDGE_CANDIDATES) + list(_CHROME_CANDIDATES)
    else:
        candidates = list(_CHROME_CANDIDATES) + list(_EDGE_CANDIDATES)
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("未找到本机 Chrome/Edge，请安装 Google Chrome。")


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _free_port(preferred: int = DEFAULT_CDP_PORT) -> int:
    if not _port_open(preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_port(port: int, timeout_s: float = 30.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _port_open(port):
            return True
        time.sleep(0.25)
    return False


def clear_stale_profile_locks(profile_dir: Path) -> None:
    profile_dir = Path(profile_dir)
    if not profile_dir.exists():
        return
    for name in ("SingletonLock", "SingletonCookie", "SingletonSocket", "lockfile"):
        path = profile_dir / name
        try:
            if path.exists() or path.is_symlink():
                path.unlink(missing_ok=True)
                _safe_print(f"cleared stale lock: {path.name}")
        except Exception as exc:  # noqa: BLE001
            _safe_print(f"lock clear skip {name}: {exc}")


def launch_browser(
    p: Playwright,
    *,
    headed: bool = True,
    channel: str | None = "chrome",
) -> tuple[Browser, str]:
    launch_kwargs = {
        "headless": not headed,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
        ],
    }
    candidates: list[str | None] = []
    if channel:
        candidates.append(channel)
    for item in PREFERRED_CHANNELS:
        if item not in candidates:
            candidates.append(item)
    candidates.append(None)

    last_exc: Exception | None = None
    for candidate in candidates:
        try:
            if candidate:
                browser = p.chromium.launch(channel=candidate, **launch_kwargs)
                return browser, candidate
            browser = p.chromium.launch(**launch_kwargs)
            return browser, "chromium"
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            continue
    raise RuntimeError(f"Unable to launch browser: {last_exc}")


def _launch_via_cdp(
    p: Playwright,
    *,
    profile_dir: Path,
    site_cfg: SiteConfig,
    headed: bool,
    channel: str | None,
) -> tuple[BrowserContext, str, subprocess.Popen | None]:
    profile_dir = profile_dir_for_path(profile_dir)
    clear_stale_profile_locks(profile_dir)

    # Reuse already-open debug Chrome (avoids ProcessSingleton lock fights).
    if _port_open(DEFAULT_CDP_PORT):
        try:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{DEFAULT_CDP_PORT}")
            context = browser.contexts[0] if browser.contexts else browser.new_context(
                locale=site_cfg.locale,
                viewport={"width": 1440, "height": 900},
            )
            try:
                context.add_init_script(_STEALTH_JS)
            except Exception:
                pass
            _safe_print(f"CDP reused port={DEFAULT_CDP_PORT} profile={profile_dir}")
            return context, "chrome-cdp-reuse", None
        except Exception as exc:  # noqa: BLE001
            _safe_print(f"CDP reuse failed: {exc!s}")

    exe = _find_browser_exe(channel)
    label = "chrome-cdp" if "chrome" in exe.name.lower() else "edge-cdp"
    cdp_port = _free_port(DEFAULT_CDP_PORT)
    log_path = profile_dir / "chrome-launch.log"

    # Important: keep args ASCII-friendly. Profile path must be ASCII.
    args = [
        str(exe),
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=Translate,MediaRouter",
        "--new-window",
        site_cfg.base_url + "/",
    ]
    if not headed:
        args.append("--headless=new")

    env = os.environ.copy()
    # Avoid inheriting CHROME_USER_DATA weirdness.
    env.pop("CHROME_USER_DATA_DIR", None)

    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write("CMD: " + " ".join(args) + "\n")
        log.flush()
        proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, env=env)

    # Wait for either CDP port or process death.
    deadline = time.time() + 30
    while time.time() < deadline:
        if _port_open(cdp_port):
            break
        if proc.poll() is not None:
            break
        time.sleep(0.25)

    if not _port_open(cdp_port):
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-1500:]
        if proc.poll() is None:
            proc.terminate()
        raise RuntimeError(f"Chrome CDP port {cdp_port} not ready.\n{tail}")

    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
    context = browser.contexts[0] if browser.contexts else browser.new_context(
        locale=site_cfg.locale,
        viewport={"width": 1440, "height": 900},
    )
    try:
        context.add_init_script(_STEALTH_JS)
    except Exception:
        pass
    _safe_print(f"CDP attached port={cdp_port} profile={profile_dir}")
    return context, label, proc


def profile_dir_for_path(profile_dir: Path | str) -> Path:
    """Normalize to an ASCII-safe absolute profile directory under home."""
    path = Path(profile_dir)
    name = path.name or "default"
    # Always use ASCII home root — Chrome on Windows ignores non-ASCII user-data-dir.
    mapped = ASCII_PROFILE_ROOT / name
    mapped.mkdir(parents=True, exist_ok=True)
    return mapped.resolve()


def _launch_via_playwright_persistent(
    p: Playwright,
    *,
    profile_dir: Path,
    site_cfg: SiteConfig,
    headed: bool,
    channel: str | None,
) -> tuple[BrowserContext, str, None]:
    profile_dir = profile_dir_for_path(profile_dir)
    clear_stale_profile_locks(profile_dir)
    kwargs = {
        "user_data_dir": str(profile_dir),
        "headless": not headed,
        "locale": site_cfg.locale,
        "viewport": {"width": 1440, "height": 900},
        "channel": channel or "chrome",
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        "ignore_default_args": ["--enable-automation"],
    }
    context = p.chromium.launch_persistent_context(**kwargs)
    context.add_init_script(_STEALTH_JS)
    _safe_print(f"Playwright persistent context profile={profile_dir}")
    return context, f"playwright-{(channel or 'chrome')}", None


def launch_persistent_context(
    p: Playwright,
    *,
    profile_dir: Path,
    site_cfg: SiteConfig,
    headed: bool = True,
    channel: str | None = "chrome",
    cdp_port: int = DEFAULT_CDP_PORT,
) -> tuple[BrowserContext, str, subprocess.Popen | None]:
    _ = cdp_port
    try:
        return _launch_via_cdp(
            p,
            profile_dir=profile_dir,
            site_cfg=site_cfg,
            headed=headed,
            channel=channel,
        )
    except Exception as cdp_exc:  # noqa: BLE001
        _safe_print(f"CDP launch failed, fallback Playwright persistent: {cdp_exc!s}")
        return _launch_via_playwright_persistent(
            p,
            profile_dir=profile_dir,
            site_cfg=site_cfg,
            headed=headed,
            channel=channel,
        )


def new_context(browser: Browser, site_cfg: SiteConfig, *, storage_state: str | None = None):
    kwargs = {
        "locale": site_cfg.locale,
        "viewport": {"width": 1440, "height": 900},
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "extra_http_headers": {"Accept-Language": "en-US,en;q=0.9"},
    }
    if storage_state:
        kwargs["storage_state"] = storage_state
    context = browser.new_context(**kwargs)
    context.add_init_script(_STEALTH_JS)
    return context
