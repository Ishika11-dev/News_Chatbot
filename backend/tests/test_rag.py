import pytest
from datetime import datetime, timezone, timedelta
from langchain_core.documents import Document
from app.core.langchain_rag import format_docs_with_citations
from app.utils.date_utils import get_cutoff_timestamp, datetime_to_epoch

def test_rag_context_formatting():
    """Verifies that retrieved chunks are cleanly numbered and structured for prompt injection."""
    docs = [
        Document(
            page_content="Google has announced major advancements in its multimodal AI capabilities.",
            metadata={
                "article_id": "art-1",
                "title": "Google Unveils New AI Features",
                "publisher": "TechCrunch",
                "published_at": "2026-11-05T12:00:00Z",
                "url": "https://techcrunch.com/google-ai",
                "category": "Technology"
            }
        ),
        Document(
            page_content="OpenAI expanded its API platform with new tooling for enterprise agents.",
            metadata={
                "article_id": "art-2",
                "title": "OpenAI Launches Enterprise Tools",
                "publisher": "The Verge",
                "published_at": "2026-11-06T15:30:00Z",
                "url": "https://theverge.com/openai-tools",
                "category": "Technology"
            }
        )
    ]

    context_str, sources = format_docs_with_citations(docs)
    assert "[1] Title: Google Unveils New AI Features" in context_str
    assert "TechCrunch" in context_str
    assert "[2] Title: OpenAI Launches Enterprise Tools" in context_str
    assert "The Verge" in context_str
    assert len(sources) == 2

def test_rag_fallback_when_empty():
    """Verifies that an empty retrieval yields empty context."""
    context_str, sources = format_docs_with_citations([])
    assert context_str == "No recent news articles found for this topic."
    assert sources == []

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
