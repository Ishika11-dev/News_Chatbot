"""
URL canonicalization and SHA-256 article identifier generation.
"""

import hashlib
from typing import Set, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "source", "feed"
}


def canonicalize_url(url: str) -> str:
    """Strips tracking query parameters and standardizes the URL."""
    if not url:
        return ""
    url = url.strip()
    parsed = urlparse(url)
    clean_queries = [
        (k, v) for k, v in parse_qsl(parsed.query)
        if k.lower() not in TRACKING_PARAMS
    ]
    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        parsed.params,
        urlencode(clean_queries, doseq=True),
        ""
    ))


def generate_article_id(canonical_url: str) -> str:
    """Generates a stable SHA-256 identifier from a canonical URL."""
    return hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()


class ArticleDeduplicator:
    """In-memory cache of seen article identifiers to prevent duplicate ingestion."""

    def __init__(self, seen_ids: Optional[Set[str]] = None):
        self.seen_ids = set(seen_ids) if seen_ids is not None else set()

    def is_seen(self, article_id: str) -> bool:
        return article_id in self.seen_ids

    def mark_seen(self, article_id: str):
        self.seen_ids.add(article_id)

