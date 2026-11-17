"""
RSS feed configuration loader and HTTP fetcher.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import requests
import feedparser

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 NewsIntelligence/1.0",
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8"
}


class FeedFetcher:
    """Loads configured RSS feeds and fetches their XML feeds via HTTP."""

    def __init__(self, config_path: str = "feeds.yaml"):
        self.config_path = Path(config_path)

    def load_feed_configs(self) -> List[Dict[str, Any]]:
        """Loads feed list from YAML file with fallback resolution."""
        path = self.config_path
        if not path.exists():
            # Try looking one or two directories up
            alt1 = Path(__file__).resolve().parent.parent.parent / path.name
            alt2 = Path(__file__).resolve().parent.parent / path.name
            if alt1.exists():
                path = alt1
            elif alt2.exists():
                path = alt2

        if not path.exists():
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("feeds", [])

    def fetch_feed(self, url: str, timeout: int = 12) -> Optional[feedparser.FeedParserDict]:
        """Fetches and parses a single RSS feed."""
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=timeout)
            resp.raise_for_status()
            return feedparser.parse(resp.content)
        except Exception as e:
            print(f"[!] Warning: Failed to fetch feed '{url}': {e}")
            return None

