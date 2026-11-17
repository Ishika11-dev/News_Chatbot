"""
Article content extractor combining RSS feed payloads and Trafilatura web scraping.
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
    Extracts article title, summary, and body text from RSS feed entries,
    with an optional full-webpage scrape via Trafilatura.
    """

    def __init__(self, enable_trafilatura: bool = False):
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
        Returns None if Trafilatura is unavailable or extraction fails.
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
                if result and len(result.strip()) > 100:
                    return result.strip()
        except Exception:
            pass

        return None

    def extract_article(self, entry: Dict[str, Any], link: str) -> tuple[str, str]:
        """
        High-level extraction: gets RSS title/content, optionally enhancing with
        full-text Trafilatura scrape if configured and available.
        """
        title, body = self.extract_from_rss_entry(entry)

        if self.enable_trafilatura and link:
            full_text = self.extract_with_trafilatura(link)
            if full_text and len(full_text) > len(body):
                body = full_text

        return title, body

