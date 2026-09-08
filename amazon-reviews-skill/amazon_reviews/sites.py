"""Amazon marketplace site configs."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class SiteConfig:
    code: str
    host: str
    locale: str
    currency_hint: str

    @property
    def base_url(self) -> str:
        return f"https://www.{self.host}"

    def product_url(self, asin: str) -> str:
        return f"{self.base_url}/dp/{asin}"

    def reviews_url(
        self,
        asin: str,
        *,
        page: int = 1,
        sort_by: str = "recent",
        filter_by_star: str | None = None,
        reviewer_type: str = "all_reviews",
        keyword: str | None = None,
        media_only: bool = False,
    ) -> str:
        params = [
            "ie=UTF8",
            f"reviewerType={reviewer_type}",
            f"sortBy={sort_by}",
            f"pageNumber={page}",
        ]
        if filter_by_star:
            params.append(f"filterByStar={filter_by_star}")
        if keyword:
            params.append(f"filterByKeyword={quote_plus(keyword)}")
        if media_only:
            params.append("mediaReviewsOnly=true")
        query = "&".join(params)
        return f"{self.base_url}/product-reviews/{asin}/ref=cm_cr_arp_d_viewopt_srt?{query}"


SITES: dict[str, SiteConfig] = {
    "com": SiteConfig("com", "amazon.com", "en_US", "USD"),
    "co.uk": SiteConfig("co.uk", "amazon.co.uk", "en_GB", "GBP"),
    "de": SiteConfig("de", "amazon.de", "de_DE", "EUR"),
    "fr": SiteConfig("fr", "amazon.fr", "fr_FR", "EUR"),
    "it": SiteConfig("it", "amazon.it", "it_IT", "EUR"),
    "es": SiteConfig("es", "amazon.es", "es_ES", "EUR"),
    "ca": SiteConfig("ca", "amazon.ca", "en_CA", "CAD"),
    "com.au": SiteConfig("com.au", "amazon.com.au", "en_AU", "AUD"),
    "co.jp": SiteConfig("co.jp", "amazon.co.jp", "ja_JP", "JPY"),
    "in": SiteConfig("in", "amazon.in", "en_IN", "INR"),
    "com.mx": SiteConfig("com.mx", "amazon.com.mx", "es_MX", "MXN"),
}


def get_site(code: str) -> SiteConfig:
    key = code.strip().lower().lstrip(".")
    if key.startswith("amazon."):
        key = key[len("amazon.") :]
    if key not in SITES:
        supported = ", ".join(sorted(SITES))
        raise KeyError(f"Unknown site '{code}'. Supported: {supported}")
    return SITES[key]


def list_site_codes() -> list[str]:
    return sorted(SITES.keys())
