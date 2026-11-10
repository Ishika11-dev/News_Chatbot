import pytest
from datetime import datetime, timezone, timedelta
from app.core.rag_engine import NewsRAGEngine
from app.utils.date_utils import get_cutoff_timestamp, datetime_to_epoch

def test_rag_context_formatting():
    """Verifies that retrieved chunks are cleanly numbered and structured for prompt injection."""
    engine = NewsRAGEngine()
    mock_hits = [
        {
            "score": 0.88,
            "payload": {
                "title": "Google Unveils New AI Features",
                "publisher": "TechCrunch",
                "published_at": "2026-11-05T12:00:00Z",
                "text": "Google has announced major advancements in its multimodal AI capabilities.",
                "article_url": "https://techcrunch.com/google-ai"
            }
        },
        {
            "score": 0.81,
            "payload": {
                "title": "OpenAI Launches Enterprise Tools",
                "publisher": "The Verge",
                "published_at": "2026-11-06T15:30:00Z",
                "text": "OpenAI expanded its API platform with new tooling for enterprise agents.",
                "article_url": "https://theverge.com/openai-tools"
            }
        }
    ]

    context_str = engine._build_context_block(mock_hits)
    assert "[1] Title: Google Unveils New AI Features" in context_str
    assert "TechCrunch" in context_str
    assert "[2] Title: OpenAI Launches Enterprise Tools" in context_str
    assert "The Verge" in context_str

def test_rag_fallback_when_empty():
    """Verifies that an empty retrieval yields the standard safe message."""
    engine = NewsRAGEngine()
    context_str = engine._build_context_block([])
    assert "No recent news articles matched your search." in context_str

def test_30_day_cutoff_enforcement():
    """Validates that cutoff epoch correctly separates fresh news from expired news."""
    now_utc = datetime.now(timezone.utc)
    twenty_days_ago = now_utc - timedelta(days=20)
    thirty_five_days_ago = now_utc - timedelta(days=35)

    cutoff = get_cutoff_timestamp(retention_days=30)

    # 20 days ago should be retained (gte cutoff)
    assert datetime_to_epoch(twenty_days_ago) >= cutoff
    # 35 days ago should be expired (lt cutoff)
    assert datetime_to_epoch(thirty_five_days_ago) < cutoff

