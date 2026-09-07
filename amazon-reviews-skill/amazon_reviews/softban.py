"""Soft-ban / login-wall detection for Amazon review pages."""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

SOFTBAN_PATTERNS = [
    r"We limit review access when we detect unusual activity",
    r"Send a request so we can verify your account",
    r"restore the full reviews experience",
    r"unusual activity on an account",
]

LOGIN_PATTERNS = [
    r'name="email"',
    r'id="ap_email"',
    r'id="ap_password"',
    r"Sign in",
    r"/ap/signin",
]

CAPTCHA_PATTERNS = [
    r"validateCaptcha",
    r"opfcaptcha",
    r"Enter the characters you see",
    r"Type the characters you see",
]

EDGEX_PATTERNS = [
    r"edgex/guard",
    r"Getting things ready",
    r"__rx_csd=",
]


@dataclass
class PageHealth:
    ok: bool
    softbanned: bool = False
    needs_login: bool = False
    captcha: bool = False
    edgex_challenge: bool = False
    reason: str = ""
    review_count_on_page: int = 0
    has_pagination: bool = False
    has_star_filters: bool = False


def _text_matches(html: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        if re.search(pattern, html, flags=re.IGNORECASE):
            return pattern
    return None


def assess_review_page(html: str, *, soup: BeautifulSoup | None = None) -> PageHealth:
    soup = soup or BeautifulSoup(html, "lxml")
    reviews = soup.select('[data-hook="review"]')
    review_count = len(reviews)

    soft = _text_matches(html, SOFTBAN_PATTERNS)
    if soft:
        return PageHealth(
            ok=False,
            softbanned=True,
            reason=f"softban matched: {soft}",
            review_count_on_page=review_count,
        )

    # Softban often removes sort/filter chrome and caps ~8 reviews without saying so.
    has_pagination = bool(
        soup.select_one("ul.a-pagination")
        or soup.select_one('[data-hook="pagination-bar"]')
        or soup.select_one("li.a-last a")
    )
    has_star_filters = bool(
        soup.select_one("#histogramTable")
        or soup.select_one('[data-hook="reviews-medley-footer"]')
        or soup.select('a[href*="filterByStar="]')
    )

    # EdgeX interstitial (HTTP clients usually stick here).
    edgex = _text_matches(html, EDGEX_PATTERNS)
    if edgex and review_count == 0:
        return PageHealth(
            ok=False,
            edgex_challenge=True,
            reason=f"edgex challenge matched: {edgex}",
            review_count_on_page=0,
            has_pagination=has_pagination,
            has_star_filters=has_star_filters,
        )

    captcha = _text_matches(html, CAPTCHA_PATTERNS)
    if captcha and review_count == 0:
        return PageHealth(
            ok=False,
            captcha=True,
            reason=f"captcha matched: {captcha}",
            review_count_on_page=0,
            has_pagination=has_pagination,
            has_star_filters=has_star_filters,
        )

    login = _text_matches(html, LOGIN_PATTERNS)
    # Login wall: sign-in form and no reviews.
    if review_count == 0 and login and (
        soup.select_one("#ap_email")
        or soup.select_one("#ap_password")
        or soup.select_one('form[name="signIn"]')
        or "/ap/signin" in html
    ):
        return PageHealth(
            ok=False,
            needs_login=True,
            reason="login wall / session expired",
            review_count_on_page=0,
            has_pagination=has_pagination,
            has_star_filters=has_star_filters,
        )

    # Heuristic soft degradation: tiny review slice and no filter/pagination chrome
    # on what should be a full reviews listing page.
    if (
        0 < review_count <= 8
        and not has_pagination
        and not has_star_filters
        and "product-reviews" in html
    ):
        # Not definitive alone — callers combine with filter-matrix behavior.
        return PageHealth(
            ok=True,
            softbanned=False,
            reason="possible_soft_degradation",
            review_count_on_page=review_count,
            has_pagination=has_pagination,
            has_star_filters=has_star_filters,
        )

    return PageHealth(
        ok=True,
        review_count_on_page=review_count,
        has_pagination=has_pagination,
        has_star_filters=has_star_filters,
    )
