"""
Unit tests for the modular ingestion architecture (app.ingestion).
Verifies:
- Individual modules (feed_fetcher, content_extractor, text_cleaner, date_utils, deduplicator, document_builder, chunker)
- 30-day retention gate & missing/invalid date rejection (Requirement 7)
- End-to-end NewsIngestionPipeline assembly
"""

import pytest
from datetime import datetime, timezone, timedelta
from langchain_core.documents import Document

from app.ingestion.text_cleaner import clean_html, normalize_whitespace, TextCleaner
from app.ingestion.date_utils import (
    parse_date_to_utc,
    get_cutoff_timestamp,
    is_within_retention_window
)
from app.ingestion.deduplicator import (
    canonicalize_url,
    generate_article_id,
    ArticleDeduplicator
)
from app.ingestion.document_builder import DocumentBuilder
from app.ingestion.chunker import ArticleChunker
from app.ingestion.content_extractor import ContentExtractor
from app.ingestion.feed_fetcher import FeedFetcher
from app.ingestion.pipeline import NewsIngestionPipeline


# ============================================================================
# 1. Text Cleaner Tests
# ============================================================================

def test_clean_html_strips_unwanted_tags():
    raw_html = (
        "<div><script>alert('xss');</script>"
        "<p>Breaking: <b>Tech revolution</b> continues.</p>"
        "<style>body { color: red; }</style>"
        "<iframe>http://spam.com</iframe></div>"
    )
    cleaned = clean_html(raw_html)
    assert "alert" not in cleaned
    assert "body { color: red; }" not in cleaned
    assert "spam.com" not in cleaned
    assert "Breaking: Tech revolution continues." in cleaned


def test_normalize_whitespace():
    raw = "Headline   with \t irregular \n\n spaces \xa0 and tabs. "
    normalized = normalize_whitespace(raw)
    assert normalized == "Headline with irregular spaces and tabs."


def test_text_cleaner_class_wrapper():
    assert TextCleaner.clean_html("<p>Hello</p>") == "Hello"
    assert TextCleaner.normalize_whitespace("a  b") == "a b"


# ============================================================================
# 2. Date Utilities & Requirement 7 Verification
# ============================================================================

def test_date_utils_valid_utc_parsing():
    date_str = "Mon, 15 Nov 2026 10:30:00 GMT"
    iso_date, epoch_ts = parse_date_to_utc(date_str)
    assert iso_date is not None
    assert epoch_ts is not None
    assert "2026-11-15" in iso_date


def test_date_utils_missing_or_invalid_date_not_treated_as_current():
    """Requirement 7: Missing/invalid dates must NOT be treated as current news."""
    # Missing date
    iso_none, epoch_none = parse_date_to_utc(None)
    assert iso_none is None
    assert epoch_none is None
    assert not is_within_retention_window(epoch_none, retention_days=30)

    # Empty string date
    iso_empty, epoch_empty = parse_date_to_utc("   ")
    assert iso_empty is None
    assert epoch_empty is None
    assert not is_within_retention_window(epoch_empty, retention_days=30)

    # Invalid / garbage date string
    iso_bad, epoch_bad = parse_date_to_utc("NotADateStringAtAll")
    assert iso_bad is None
    assert epoch_bad is None
    assert not is_within_retention_window(epoch_bad, retention_days=30)


def test_date_utils_30_day_retention_gate():
    now_utc = datetime.now(timezone.utc)
    recent_ts = (now_utc - timedelta(days=5)).timestamp()
    expired_ts = (now_utc - timedelta(days=35)).timestamp()

    assert is_within_retention_window(recent_ts, retention_days=30)
    assert not is_within_retention_window(expired_ts, retention_days=30)
    assert not is_within_retention_window(None, retention_days=30)


# ============================================================================
# 3. Deduplicator Tests
# ============================================================================

def test_url_canonicalization_removes_tracking_params():
    url_tracked = "https://example.com/news/article-1?utm_source=twitter&utm_medium=feed&fbclid=12345"
    url_clean = "https://example.com/news/article-1"
    assert canonicalize_url(url_tracked) == url_clean


def test_generate_article_id_deterministic():
    url = "https://example.com/news/ai-breakthrough"
    id1 = generate_article_id(url)
    id2 = generate_article_id(url)
    assert id1 == id2
    assert len(id1) == 64  # SHA-256 hex length


def test_article_deduplicator_cache():
    dedup = ArticleDeduplicator()
    doc_id = "test_sha256_hash"
    assert not dedup.is_seen(doc_id)
    dedup.mark_seen(doc_id)
    assert dedup.is_seen(doc_id)


# ============================================================================
# 4. Document Builder Tests
# ============================================================================

def test_document_builder_metadata_schema():
    doc = DocumentBuilder.build(
        title="OpenAI Announces Model",
        body="Detailed body text explaining the announcement.",
        article_id="abc123hash",
        publisher="TechNews",
        published_at="2026-11-15T00:00:00+00:00",
        published_timestamp=1794700800.0,
        url="https://example.com/openai",
        category="Technology"
    )

    assert isinstance(doc, Document)
    assert "OpenAI Announces Model" in doc.page_content
    assert doc.metadata["article_id"] == "abc123hash"
    assert doc.metadata["publisher"] == "TechNews"
    assert doc.metadata["published_at"] == "2026-11-15T00:00:00+00:00"
    assert doc.metadata["published_timestamp"] == 1794700800.0
    assert doc.metadata["url"] == "https://example.com/openai"
    assert doc.metadata["category"] == "Technology"


# ============================================================================
# 5. Chunker Tests
# ============================================================================

def test_chunker_splits_and_tags_chunk_id():
    chunker = ArticleChunker(chunk_size=200, chunk_overlap=40)
    long_body = "This is a detailed paragraph about artificial intelligence advancements. " * 10
    parent_doc = Document(
        page_content=long_body,
        metadata={"article_id": "art_999", "publisher": "AI Daily"}
    )

    chunks = chunker.split_documents([parent_doc])
    assert len(chunks) > 1
    for idx, c in enumerate(chunks):
        assert c.metadata["article_id"] == "art_999"
        assert c.metadata["chunk_id"] == f"art_999_{idx}"
        assert c.metadata["publisher"] == "AI Daily"


# ============================================================================
# 6. Content Extractor Tests (Trafilatura with RSS Fallback)
# ============================================================================

def test_content_extractor_rss_fallback():
    extractor = ContentExtractor(enable_trafilatura=False)
    fake_entry = {
        "title": "Quantum Computing Breakthrough",
        "summary": "Scientists have achieved quantum advantage with a new chip.",
        "content": [{"value": "<p>Full article body inside content:encoded tag.</p>"}]
    }

    title, body = extractor.extract_article(fake_entry, link="https://example.com/quantum")
    assert title == "Quantum Computing Breakthrough"
    assert "Full article body inside content:encoded tag." in body


# ============================================================================
# 7. Feed Fetcher Tests
# ============================================================================

def test_feed_fetcher_loads_yaml_configs():
    fetcher = FeedFetcher(config_path="feeds.yaml")
    feeds = fetcher.load_feed_configs()
    assert isinstance(feeds, list)
    assert len(feeds) > 0
    assert any(f.get("name") == "TechCrunch" for f in feeds)


# ============================================================================
# 8. Complete Pipeline Assembly
# ============================================================================

def test_news_ingestion_pipeline_initialization():
    pipeline = NewsIngestionPipeline(retention_days=30, chunk_size=700, chunk_overlap=100)
    feeds = pipeline.load_feed_configs()
    assert len(feeds) > 0
    assert hasattr(pipeline, "chunk_documents")
    assert hasattr(pipeline, "fetch_articles_as_documents")
    assert hasattr(pipeline, "load_and_chunk_news")

