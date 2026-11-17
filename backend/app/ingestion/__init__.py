"""
Modular News Ingestion Package for AI-Powered News Intelligence Chatbot.
Single source of truth for all news fetching, extraction, deduplication, and chunking.
"""

from app.ingestion.feed_fetcher import FeedFetcher, REQUEST_HEADERS
from app.ingestion.content_extractor import ContentExtractor
from app.ingestion.text_cleaner import clean_html, normalize_whitespace, TextCleaner
from app.ingestion.date_utils import parse_date_to_utc, get_cutoff_timestamp, is_within_retention_window
from app.ingestion.deduplicator import canonicalize_url, generate_article_id, ArticleDeduplicator, TRACKING_PARAMS
from app.ingestion.document_builder import DocumentBuilder
from app.ingestion.chunker import ArticleChunker
from app.ingestion.pipeline import NewsIngestionPipeline

__all__ = [
    "FeedFetcher",
    "REQUEST_HEADERS",
    "ContentExtractor",
    "clean_html",
    "normalize_whitespace",
    "TextCleaner",
    "parse_date_to_utc",
    "get_cutoff_timestamp",
    "is_within_retention_window",
    "canonicalize_url",
    "generate_article_id",
    "ArticleDeduplicator",
    "TRACKING_PARAMS",
    "DocumentBuilder",
    "ArticleChunker",
    "NewsIngestionPipeline",
]
