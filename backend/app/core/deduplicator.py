import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from typing import Set, Optional
from app.utils.logger import logger

class ArticleDeduplicator:
    """Detects and prevents duplicate article ingestion using URL canonicalization and hashing."""

    TRACKING_PARAMS = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "ref", "source", "feed"
    }

    def __init__(self):
        self._seen_ids: Set[str] = set()

    @staticmethod
    def canonicalize_url(url: str) -> str:
        """Strips tracking query parameters and standardizes scheme/domain."""
        if not url:
            return ""

        url = url.strip()
        parsed = urlparse(url)
        filtered_queries = [
            (k, v) for k, v in parse_qsl(parsed.query)
            if k.lower() not in ArticleDeduplicator.TRACKING_PARAMS
        ]

        clean_path = parsed.path.rstrip("/")
        clean_url = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            clean_path,
            parsed.params,
            urlencode(filtered_queries, doseq=True),
            ""
        ))
        return clean_url

    @classmethod
    def generate_article_id(cls, canonical_url: str, title: Optional[str] = None) -> str:
        """
        Generates a deterministic unique ID for the article.
        Uses SHA-256 hash of canonical URL; if URL is missing, falls back to normalized title.
        """
        source_key = canonical_url if canonical_url else (title or "").lower().strip()
        return hashlib.sha256(source_key.encode("utf-8")).hexdigest()

    def is_duplicate(self, article_id: str) -> bool:
        """Checks if the article has already been processed in the current run."""
        return article_id in self._seen_ids

    def register_seen(self, article_id: str) -> None:
        """Registers an article ID as seen."""
        self._seen_ids.add(article_id)

    def load_existing_ids(self, ids: Set[str]) -> None:
        """Loads a set of existing article IDs (e.g. from database or vector store)."""
        self._seen_ids.update(ids)
        logger.info(f"Loaded {len(ids)} existing article IDs into deduplicator cache.")

