"""
Clean RSS Content and Summary Extractor.
Extracts high-signal, dense article titles and executive summaries directly
from RSS feed entries without slow, error-prone external web scraping.
"""

from typing import Dict, Any, Optional
from app.ingestion.text_cleaner import clean_html


class ContentExtractor:
    """
    Extracts article title and clean executive summary from RSS entry payloads.
    Provides fast, deterministic extraction with zero external network overhead.
    """

    def __init__(self):
        pass

    def extract_from_rss_entry(self, entry: Dict[str, Any]) -> tuple[str, str]:
        """
        Extracts title and clean executive summary from an RSS feed entry dictionary.
        Prioritizes summary/description for dense, high-signal RAG retrieval.
        """
        raw_title = entry.get("title", "")
        raw_summary = entry.get("summary", "") or entry.get("description", "")
        raw_content = ""

        # Check content only if summary is completely absent
        if not raw_summary:
            content_list = entry.get("content", [])
            if content_list and isinstance(content_list, list):
                raw_content = content_list[0].get("value", "")

        clean_title = clean_html(raw_title)
        clean_body = clean_html(raw_summary or raw_content)

        # Ensure summary is concise and high-signal (capping around ~600-800 chars for 1 clean chunk)
        if len(clean_body) > 800:
            period_idx = clean_body.rfind(".", 0, 700)
            if period_idx > 200:
                clean_body = clean_body[: period_idx + 1]
            else:
                clean_body = clean_body[:600]

        return clean_title, clean_body

    def extract_article(self, entry: Dict[str, Any], link: Optional[str] = None) -> tuple[str, str]:
        """
        Extracts title and summary directly from the RSS feed entry payload.
        Zero external web scraping, zero cookie walls, zero ad noise.
        """
        return self.extract_from_rss_entry(entry)
