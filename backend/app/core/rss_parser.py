import yaml
import feedparser
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.schemas.news import FeedConfig, CleanedArticle
from app.core.preprocessor import TextPreprocessor
from app.core.deduplicator import ArticleDeduplicator
from app.utils.date_utils import parse_date_to_utc, datetime_to_epoch, is_within_retention_window
from app.utils.logger import logger
from app.config import settings

class RSSParser:
    """Fetches, parses, cleans, and standardizes news articles from RSS feeds."""

    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 NewsIntelligence/1.0",
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8"
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or settings.FEEDS_CONFIG_PATH
        self.feeds: List[FeedConfig] = self._load_feed_configs()

    def _load_feed_configs(self) -> List[FeedConfig]:
        """Loads feed configurations from YAML file."""
        path = Path(self.config_path)
        if not path.exists():
            logger.warning(f"Feeds configuration not found at {path}. Using default list.")
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                feed_list = data.get("feeds", [])
                return [FeedConfig(**feed) for feed in feed_list]
        except Exception as e:
            logger.error(f"Failed to load feeds configuration: {e}")
            return []

    @staticmethod
    def _extract_image_url(entry: Dict[str, Any]) -> Optional[str]:
        """Extracts article thumbnail or image URL from RSS media tags."""
        media = entry.get("media_content", [])
        if media and isinstance(media, list) and len(media) > 0:
            url = media[0].get("url")
            if url:
                return url

        thumbs = entry.get("media_thumbnail", [])
        if thumbs and isinstance(thumbs, list) and len(thumbs) > 0:
            url = thumbs[0].get("url")
            if url:
                return url

        enclosures = entry.get("enclosures", [])
        for enc in enclosures:
            if enc.get("type", "").startswith("image/"):
                return enc.get("href")

        return None

    def fetch_feed_articles(self, feed_cfg: FeedConfig, deduplicator: Optional[ArticleDeduplicator] = None) -> List[CleanedArticle]:
        """Fetches and cleans all new, valid articles from a single RSS feed."""
        logger.info(f"Fetching RSS feed: {feed_cfg.name} ({feed_cfg.url})")
        articles: List[CleanedArticle] = []

        try:
            resp = requests.get(feed_cfg.url, headers=self.REQUEST_HEADERS, timeout=12)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
        except Exception as e:
            logger.error(f"Error fetching feed '{feed_cfg.name}': {e}")
            return []

        if parsed.bozo and not parsed.entries:
            logger.warning(f"Feed '{feed_cfg.name}' parsing error or empty entries.")
            return []

        for entry in parsed.entries:
            try:
                link = entry.get("link", "").strip()
                if not link:
                    continue
                canonical_url = ArticleDeduplicator.canonicalize_url(link)
                article_id = ArticleDeduplicator.generate_article_id(canonical_url, entry.get("title"))

                if deduplicator and deduplicator.is_duplicate(article_id):
                    continue

                published_raw = entry.get("published") or entry.get("pubDate") or entry.get("updated")
                published_dt = parse_date_to_utc(published_raw)

                # Enforce 30-day window check upfront
                if not is_within_retention_window(published_dt, retention_days=settings.RETENTION_DAYS):
                    continue

                raw_title = entry.get("title", "")
                raw_summary = entry.get("summary", "") or entry.get("description", "")

                raw_content = ""
                content_list = entry.get("content", [])
                if content_list and isinstance(content_list, list):
                    raw_content = content_list[0].get("value", "")

                clean_title, clean_summary, clean_content, is_valid = TextPreprocessor.clean_article(
                    raw_title=raw_title,
                    raw_summary=raw_summary,
                    raw_content=raw_content
                )

                if not is_valid:
                    continue

                author = entry.get("author") or entry.get("creator")
                image_url = self._extract_image_url(entry)

                article = CleanedArticle(
                    article_id=article_id,
                    title=clean_title,
                    content=clean_content,
                    summary=clean_summary or clean_content[:250],
                    publisher=feed_cfg.publisher,
                    published_at=published_dt,
                    published_timestamp=datetime_to_epoch(published_dt),
                    category=feed_cfg.category,
                    article_url=canonical_url,
                    author=author,
                    image_url=image_url
                )

                if deduplicator:
                    deduplicator.register_seen(article_id)

                articles.append(article)

            except Exception as item_err:
                logger.debug(f"Failed processing item from {feed_cfg.name}: {item_err}")
                continue

        logger.info(f"Feed '{feed_cfg.name}': extracted {len(articles)} fresh articles.")
        return articles

    def fetch_all_feeds(self, deduplicator: Optional[ArticleDeduplicator] = None) -> List[CleanedArticle]:
        """Iterates over all configured feeds and aggregates new cleaned articles."""
        all_articles: List[CleanedArticle] = []
        for feed in self.feeds:
            feed_articles = self.fetch_feed_articles(feed, deduplicator=deduplicator)
            all_articles.extend(feed_articles)
        logger.info(f"Total articles extracted across all feeds: {len(all_articles)}")
        return all_articles

