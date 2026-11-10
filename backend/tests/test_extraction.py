import pytest
from datetime import datetime, timezone, timedelta
from app.core.preprocessor import TextPreprocessor
from app.core.deduplicator import ArticleDeduplicator
from app.core.chunker import ArticleChunker
from app.core.rss_parser import RSSParser
from app.schemas.news import CleanedArticle
from app.utils.date_utils import (
    parse_date_to_utc,
    datetime_to_epoch,
    is_within_retention_window,
    get_cutoff_timestamp
)

def test_text_preprocessor_html_cleaning():
    html_input = "<p>This is a <b>great</b> news article.<script>alert('test')</script></p>"
    cleaned = TextPreprocessor.clean_html(html_input)
    assert "alert" not in cleaned
    assert "This is a great news article." in cleaned

def test_text_preprocessor_whitespace():
    raw = "Headline \n\n with   irregular   spaces \xa0 and tabs.\t"
    normalized = TextPreprocessor.normalize_whitespace(raw)
    assert normalized == "Headline with irregular spaces and tabs."

def test_article_validation():
    title, summary, content, is_valid = TextPreprocessor.clean_article(
        raw_title="Short",
        raw_summary="Too short",
        raw_content="Tiny"
    )
    assert not is_valid

    title, summary, content, is_valid = TextPreprocessor.clean_article(
        raw_title="AI Startup Raises Record $100M in Series A Round",
        raw_summary="A major breakthrough in autonomous AI agents has led to unprecedented investor interest.",
        raw_content="A major breakthrough in autonomous AI agents has led to unprecedented investor interest worldwide."
    )
    assert is_valid
    assert "AI Startup" in title

def test_url_canonicalization_and_deduplication():
    url1 = "https://www.theverge.com/tech/news?utm_source=twitter&utm_medium=social"
    url2 = "https://www.theverge.com/tech/news"

    clean_url1 = ArticleDeduplicator.canonicalize_url(url1)
    clean_url2 = ArticleDeduplicator.canonicalize_url(url2)
    assert clean_url1 == clean_url2

    id1 = ArticleDeduplicator.generate_article_id(clean_url1)
    id2 = ArticleDeduplicator.generate_article_id(clean_url2)
    assert id1 == id2

    dedup = ArticleDeduplicator()
    assert not dedup.is_duplicate(id1)
    dedup.register_seen(id1)
    assert dedup.is_duplicate(id1)

def test_date_utils_30_day_window():
    now_utc = datetime.now(timezone.utc)
    recent_date = now_utc - timedelta(days=10)
    old_date = now_utc - timedelta(days=40)

    assert is_within_retention_window(recent_date, retention_days=30)
    assert not is_within_retention_window(old_date, retention_days=30)

    cutoff = get_cutoff_timestamp(retention_days=30)
    assert datetime_to_epoch(recent_date) >= cutoff
    assert datetime_to_epoch(old_date) < cutoff

def test_article_chunker():
    now_utc = datetime.now(timezone.utc)
    article = CleanedArticle(
        article_id="test_id_123",
        title="NVIDIA Announces New Generation AI Chips",
        summary="A summary of the announcement.",
        content="NVIDIA has officially unveiled its new processor architecture designed specifically for large-scale generative AI workloads. " * 10,
        publisher="TechCrunch",
        published_at=now_utc,
        published_timestamp=datetime_to_epoch(now_utc),
        category="Technology",
        article_url="https://techcrunch.com/nvidia-announcement",
        author="Jane Doe",
        image_url="https://techcrunch.com/image.jpg"
    )

    chunker = ArticleChunker(chunk_size=400, chunk_overlap=80)
    chunks = chunker.chunk_article(article)
    assert len(chunks) > 1
    assert chunks[0].article_id == "test_id_123"
    assert chunks[0].publisher == "TechCrunch"
    assert chunks[0].category == "Technology"
    assert chunks[0].article_url == "https://techcrunch.com/nvidia-announcement"

def test_rss_parser_feeds_config():
    parser = RSSParser()
    assert len(parser.feeds) > 0
    names = [f.name for f in parser.feeds]
    assert "TechCrunch" in names
    assert "BBC News" in [f.publisher for f in parser.feeds]

