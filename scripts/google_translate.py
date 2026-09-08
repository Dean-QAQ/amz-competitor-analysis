#!/usr/bin/env python3
from __future__ import annotations

import html as html_lib
import json
import re
import sys
from urllib.parse import quote

from curl_cffi import requests

PROXY_URL = "http://127.0.0.1:7897"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://translate.google.com/",
}


def read_payload() -> dict[str, str]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def strip_html(fragment: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    text = re.sub(r"</(?:div|p|li|tr|h\d)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text).replace("\xa0", " ").replace("\r", "")
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join([line for line in lines if line]).strip()


def extract_translation(html: str) -> str:
    patterns = [
        r'class="result-container"[^>]*>([\s\S]*?)</div>',
        r'id="result-container"[^>]*>([\s\S]*?)</div>',
        r'class="result-container-text"[^>]*>([\s\S]*?)</div>',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.I)
        if not match:
            continue
        text = strip_html(match.group(1))
        if text:
          return text
    return ""


def fetch_translation(text: str, source_lang: str) -> str:
    if not text:
        return ""
    source = source_lang if source_lang and source_lang != "zh" else "auto"
    attempts = [source]
    if source != "auto":
        attempts.append("auto")
    for sl in attempts:
        url = (
            "https://translate.google.com/m?sl="
            + quote(sl)
            + "&tl=zh-CN&hl=zh-CN&ie=UTF-8&oe=UTF-8&q="
            + quote(text)
        )
        for proxies in ({"http": PROXY_URL, "https": PROXY_URL}, None):
            try:
                resp = requests.get(
                    url,
                    headers=HEADERS,
                    impersonate="chrome120",
                    proxies=proxies,
                    timeout=20,
                    allow_redirects=True,
                )
                if resp.status_code != 200:
                    continue
                translated = extract_translation(resp.text)
                if not translated:
                    continue
                if translated.strip() == text.strip() and sl != "auto":
                    continue
                return translated
            except Exception:
                continue
    return ""


def main() -> int:
    payload = read_payload()
    text = str(payload.get("text") or "")
    source_lang = str(payload.get("sourceLang") or "auto")
    translated = fetch_translation(text, source_lang)
    result = {
        "ok": bool(translated),
        "translated": translated,
        "sourceLang": source_lang,
    }
    if not translated:
        result["error"] = "Google translation failed"
    sys.stdout.write(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
