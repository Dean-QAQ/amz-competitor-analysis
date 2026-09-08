"""Parse Amazon review listing HTML into structured records."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from bs4 import BeautifulSoup, Tag


@dataclass
class Review:
    review_id: str
    asin: str
    site: str
    title: str
    body: str
    rating: float | None
    date_text: str
    author: str
    verified: bool
    helpful_votes: int | None
    variant: str
    source_url: str
    filter_star: str | None
    sort_by: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_RATING_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*out of\s*5", re.I)
_HELPFUL_RE = re.compile(r"([\d,]+)\s+people?\s+found this helpful", re.I)
_ONE_HELPFUL_RE = re.compile(r"One person found this helpful", re.I)


def _text(el: Tag | None) -> str:
    if not el:
        return ""
    return " ".join(el.stripped_strings)


def _parse_rating(block: Tag) -> float | None:
    node = block.select_one(
        '[data-hook="review-star-rating"] .a-icon-alt, '
        '[data-hook="cmps-review-star-rating"] .a-icon-alt, '
        "i.review-rating .a-icon-alt, "
        ".a-icon-alt"
    )
    raw = _text(node)
    if not raw:
        return None
    m = _RATING_RE.search(raw)
    if m:
        return float(m.group(1))
    # Some locales put rating only in class a-star-N
    icon = block.select_one("i.a-icon")
    classes = icon.get("class", []) if icon else []
    for cls in classes:
        if isinstance(cls, str) and cls.startswith("a-star-"):
            try:
                return float(cls.replace("a-star-", "").replace("-", "."))
            except ValueError:
                continue
    return None


def _parse_helpful(block: Tag) -> int | None:
    node = block.select_one('[data-hook="helpful-vote-statement"]')
    raw = _text(node)
    if not raw:
        return None
    if _ONE_HELPFUL_RE.search(raw):
        return 1
    m = _HELPFUL_RE.search(raw)
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def parse_reviews(
    html: str,
    *,
    asin: str,
    site: str,
    source_url: str,
    sort_by: str,
    filter_star: str | None,
) -> list[Review]:
    soup = BeautifulSoup(html, "lxml")
    out: list[Review] = []
    for block in soup.select('[data-hook="review"]'):
        rid = block.get("id") or ""
        if rid.startswith("R") is False and block.get("id"):
            rid = str(block.get("id"))
        if not rid:
            # Fallback: nested review div id
            nested = block.select_one("[id^=R]")
            rid = nested.get("id") if nested else ""
        if not rid:
            continue

        title_el = block.select_one(
            '[data-hook="review-title"] span:not(.a-icon-alt), [data-hook="review-title"]'
        )
        # Title node often includes star text as first span; prefer last meaningful span.
        title = ""
        if title_el:
            spans = title_el.select("span")
            candidates = [_text(s) for s in spans if _text(s) and "out of 5" not in _text(s).lower()]
            title = candidates[-1] if candidates else _text(title_el)
            title = re.sub(r"^\d+(?:\.\d+)?\s*out of\s*5\s*stars\s*", "", title, flags=re.I).strip()

        body_el = block.select_one('[data-hook="review-body"]')
        body = _text(body_el)

        author = _text(block.select_one(".a-profile-name"))
        date_text = _text(block.select_one('[data-hook="review-date"]'))
        verified = bool(block.select_one('[data-hook="avp-badge"]'))
        variant = _text(block.select_one('[data-hook="format-strip"]'))

        out.append(
            Review(
                review_id=rid,
                asin=asin,
                site=site,
                title=title,
                body=body,
                rating=_parse_rating(block),
                date_text=date_text,
                author=author,
                verified=verified,
                helpful_votes=_parse_helpful(block),
                variant=variant,
                source_url=source_url,
                filter_star=filter_star,
                sort_by=sort_by,
            )
        )
    return out
