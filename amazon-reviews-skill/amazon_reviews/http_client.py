"""HTTP client: Playwright cookies + curl_cffi Chrome TLS fingerprint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from curl_cffi import requests as cf_requests

from .sites import SiteConfig

# Cookies commonly required for authenticated Amazon sessions.
AUTH_COOKIE_NAMES = {
    "session-id",
    "session-id-time",
    "session-token",
    "ubid-main",
    "at-main",
    "sess-at-main",
    "x-main",
    "csm-hit",
    "i18n-prefs",
    "lc-main",
}


def load_storage_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"storage_state missing: {path}. Run: python -m amazon_reviews.cli login --account <id> --site com"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def cookies_for_site(storage_state: dict[str, Any], site: SiteConfig) -> list[dict[str, Any]]:
    host = site.host
    out: list[dict[str, Any]] = []
    for cookie in storage_state.get("cookies", []):
        domain = str(cookie.get("domain") or "").lstrip(".")
        if host.endswith(domain) or domain.endswith(host) or host == domain:
            out.append(cookie)
            continue
        # amazon.com cookies sometimes stored as .amazon.com
        if domain.endswith("amazon." + site.code) or domain == "amazon." + site.code:
            out.append(cookie)
    return out


def build_cookie_header(cookies: list[dict[str, Any]]) -> str:
    pairs: list[str] = []
    seen: set[str] = set()
    for cookie in cookies:
        name = cookie.get("name")
        value = cookie.get("value")
        if not name or value is None:
            continue
        # Prefer last occurrence for rotated tokens.
        if name in seen:
            pairs = [p for p in pairs if not p.startswith(f"{name}=")]
        seen.add(name)
        pairs.append(f"{name}={value}")
    return "; ".join(pairs)


class ReviewHttpClient:
    def __init__(
        self,
        site: SiteConfig,
        storage_state_path: Path,
        *,
        impersonate: str = "chrome131",
        timeout: float = 30.0,
    ) -> None:
        self.site = site
        self.storage_state_path = Path(storage_state_path)
        self.impersonate = impersonate
        self.timeout = timeout
        self.session = cf_requests.Session()
        self._apply_storage_state()

    def _apply_storage_state(self) -> None:
        state = load_storage_state(self.storage_state_path)
        cookies = cookies_for_site(state, self.site)
        if not cookies:
            raise RuntimeError(
                f"No cookies for host {self.site.host} in {self.storage_state_path}"
            )
        # Warm jar via curl_cffi cookies API when available; also keep header fallback.
        for cookie in cookies:
            try:
                self.session.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie.get("domain") or self.site.host,
                    path=cookie.get("path") or "/",
                )
            except Exception:
                pass
        self._cookie_header = build_cookie_header(cookies)

    def get(self, url: str) -> cf_requests.Response:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "upgrade-insecure-requests": "1",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "cookie": self._cookie_header,
            "referer": self.site.base_url + "/",
        }
        return self.session.get(
            url,
            headers=headers,
            timeout=self.timeout,
            impersonate=self.impersonate,
            allow_redirects=True,
        )
