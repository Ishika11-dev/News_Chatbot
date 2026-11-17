"""
Article content extractor combining Trafilatura web scraping and RSS feed payloads.
Implements Trafilatura-first extraction with graceful RSS fallback.
"""

from typing import Dict, Any, Optional
from app.ingestion.text_cleaner import clean_html

# Optional Trafilatura support for full webpage extraction
try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False


class ContentExtractor:
    """
    Extracts article title, summary, and body text.
    Prioritizes full-text extraction via Trafilatura, falling back
    to RSS feed content/summary when Trafilatura is unavailable or fails.
    """

    def __init__(self, enable_trafilatura: bool = True):
        self.enable_trafilatura = enable_trafilatura and HAS_TRAFILATURA

    def extract_from_rss_entry(self, entry: Dict[str, Any]) -> tuple[str, str]:
        """
        Extracts title and content from an RSS feed entry dictionary.
        Checks <content:encoded>, then summary/description.
        """
        raw_title = entry.get("title", "")
        raw_summary = entry.get("summary", "") or entry.get("description", "")
        raw_content = ""

        content_list = entry.get("content", [])
        if content_list and isinstance(content_list, list):
            raw_content = content_list[0].get("value", "")

        clean_title = clean_html(raw_title)
        clean_body = clean_html(raw_content or raw_summary)

        return clean_title, clean_body

    def extract_with_trafilatura(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        Fetches the live webpage and extracts clean body text using Trafilatura.
        Returns None if Trafilatura is unavailable, raises an error, or extraction fails.
        """
        if not HAS_TRAFILATURA or not url:
            return None

        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(
                    downloaded,
                    include_links=False,
                    include_images=False,
                    output_format="txt"
                )
                if result and len(result.strip()) >= 50:
                    return result.strip()
        except Exception:
            pass

        return None

    def extract_article(self, entry: Dict[str, Any], link: str) -> tuple[str, str]:
        """
        Trafilatura-first extraction with RSS fallback:
        1. Attempts full-text scrape from article URL via Trafilatura.
        2. Falls back to RSS feed payload if Trafilatura is unavailable,
           disabled, or yields insufficient content.
        """
        raw_title = entry.get("title", "")
        clean_title = clean_html(raw_title)

        body = ""
        # 1. Trafilatura-first
        if self.enable_trafilatura and link:
            extracted_text = self.extract_with_trafilatura(link)
            if extracted_text:
                body = extracted_text

        # 2. RSS fallback if Trafilatura produced no output
        if not body:
            _, body = self.extract_from_rss_entry(entry)

        return clean_title, body
