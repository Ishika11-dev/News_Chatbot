"""
End-to-end news ingestion pipeline orchestrating fetch, extraction, cleaning, deduplication, and chunking.
Acts as the unified entry point for all news ingestion across the application.
"""

from typing import List, Optional, Set, Dict, Any
from langchain_core.documents import Document

from app.ingestion.feed_fetcher import FeedFetcher
from app.ingestion.content_extractor import ContentExtractor
from app.ingestion.deduplicator import canonicalize_url, generate_article_id, ArticleDeduplicator
from app.ingestion.date_utils import parse_date_to_utc, is_within_retention_window
from app.ingestion.document_builder import DocumentBuilder
from app.ingestion.chunker import ArticleChunker


class NewsIngestionPipeline:
    """
    Coordinates modular components to fetch, clean, deduplicate,
    and chunk news articles into LangChain Documents.
    """

    def __init__(
        self,
        feeds_config_path: str = "feeds.yaml",
        retention_days: int = 30,
        chunk_size: int = 700,
        chunk_overlap: int = 100
    ):
        self.retention_days = retention_days
        self.fetcher = FeedFetcher(config_path=feeds_config_path)
        self.extractor = ContentExtractor()
        self.builder = DocumentBuilder()
        self.chunker = ArticleChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.text_splitter = self.chunker.text_splitter

    def load_feed_configs(self, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Returns loaded feed configurations from feeds.yaml, optionally filtered by category."""
        feeds = self.fetcher.load_feed_configs()
        if not categories:
            return feeds

        allowed = {c.strip().lower() for c in categories if c and c.strip()}
        if not allowed or "all" in allowed:
            return feeds

        return [
            f for f in feeds
            if (f.get("category") or "").strip().lower() in allowed
        ]

    def fetch_articles_as_documents(
        self,
        seen_ids: Optional[Set[str]] = None,
        categories: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        Fetches configured feeds (optionally filtered by categories), extracts valid articles
        within the 30-day retention window, deduplicates them, and wraps them into LangChain Documents.

        CRITICAL: Articles with missing or invalid publication dates are dropped and
        never automatically treated as current news.
        """
        dedup = ArticleDeduplicator(seen_ids=seen_ids)
        feeds = self.load_feed_configs(categories=categories)
        documents: List[Document] = []

        for feed in feeds:
            feed_name = feed.get("name", "Unknown")
            feed_url = feed.get("url")
            publisher = feed.get("publisher", feed_name)
            category = feed.get("category", "General")

            if not feed_url:
                continue

            parsed = self.fetcher.fetch_feed(feed_url)
            if not parsed or not parsed.entries:
                continue

            for entry in parsed.entries:
                link = entry.get("link", "").strip()
                if not link:
                    continue

                clean_url = canonicalize_url(link)
                article_id = generate_article_id(clean_url)

                # Deduplication
                if dedup.is_seen(article_id):
                    continue

                # 30-Day Retention Validation & Date Parsing
                raw_date = entry.get("published") or entry.get("pubDate") or entry.get("updated")
                iso_date, epoch_ts = parse_date_to_utc(raw_date)

                # Skip articles with missing, invalid, or expired publication dates
                if iso_date is None or epoch_ts is None or not is_within_retention_window(epoch_ts, retention_days=self.retention_days):
                    continue

                # Content Extraction (Clean RSS Title + Summary)
                title, body = self.extractor.extract_article(entry, link=clean_url)

                if len(title) < 5 or len(body) < 30:
                    continue

                dedup.mark_seen(article_id)

                # Build Document with standardized metadata
                doc = self.builder.build(
                    title=title,
                    body=body,
                    article_id=article_id,
                    publisher=publisher,
                    published_at=iso_date,
                    published_timestamp=epoch_ts,
                    url=clean_url,
                    category=category
                )
                documents.append(doc)

        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Splits parent Documents into chunks with metadata and chunk_ids."""
        return self.chunker.split_documents(documents)

    def load_and_chunk_news(self, seen_ids: Optional[Set[str]] = None) -> List[Document]:
        """
        End-to-end execution:
        Fetches fresh news -> Builds Documents -> Chunks with RecursiveCharacterTextSplitter.
        """
        parent_docs = self.fetch_articles_as_documents(seen_ids=seen_ids)
        return self.chunker.split_documents(parent_docs)
