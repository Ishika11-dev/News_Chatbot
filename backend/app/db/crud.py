from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Set, Optional

from app.db.models import ArticleModel, IngestionLogModel, ChatSessionModel, ChatMessageModel
from app.schemas.news import CleanedArticle, IngestionStats

def get_existing_article_ids(db: Session) -> Set[str]:
    """Retrieves all active article IDs to avoid redundant embedding calls."""
    try:
        rows = db.query(ArticleModel.article_id).all()
        return {r[0] for r in rows}
    except Exception:
        return set()

def save_articles(db: Session, articles: List[CleanedArticle]) -> int:
    """Inserts new cleaned articles into the database."""
    saved_count = 0
    for a in articles:
        db_article = ArticleModel(
            article_id=a.article_id,
            title=a.title,
            content=a.content,
            summary=a.summary,
            publisher=a.publisher,
            published_at=a.published_at,
            published_timestamp=a.published_timestamp,
            category=a.category,
            article_url=a.article_url,
            author=a.author,
            image_url=a.image_url,
            ingested_at=a.ingested_at,
            is_expired=False
        )
        db.merge(db_article)
        saved_count += 1
    db.commit()
    return saved_count

def get_recent_articles(
    db: Session,
    cutoff_timestamp: float,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[ArticleModel]:
    """Retrieves recent articles published within the 30-day window."""
    query = db.query(ArticleModel).filter(
        ArticleModel.published_timestamp >= cutoff_timestamp,
        ArticleModel.is_expired == False
    )
    if category and category.lower() != "all":
        query = query.filter(ArticleModel.category == category)

    return query.order_by(desc(ArticleModel.published_timestamp)).offset(offset).limit(limit).all()

def delete_expired_articles(db: Session, cutoff_timestamp: float) -> int:
    """Purges articles older than 30 days from the database."""
    deleted = db.query(ArticleModel).filter(
        ArticleModel.published_timestamp < cutoff_timestamp
    ).delete(synchronize_session=False)
    db.commit()
    return deleted

def log_ingestion(db: Session, stats: IngestionStats, status: str = "SUCCESS"):
    """Records ingestion run statistics."""
    log = IngestionLogModel(
        total_feeds=stats.total_feeds,
        total_fetched=stats.total_fetched,
        new_articles_ingested=stats.new_articles_ingested,
        duplicates_skipped=stats.duplicates_skipped,
        status=status,
        failed_feeds=", ".join(stats.failed_feeds) if stats.failed_feeds else None,
        duration_seconds=stats.duration_seconds
    )
    db.add(log)
    db.commit()

def save_chat_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    sources: Optional[List[dict]] = None
):
    """Saves a user or assistant message to the chat history."""
    # Ensure session exists
    session = db.query(ChatSessionModel).filter(ChatSessionModel.session_id == session_id).first()
    if not session:
        session = ChatSessionModel(session_id=session_id, title=content[:50])
        db.add(session)
        db.commit()

    msg = ChatMessageModel(
        session_id=session_id,
        role=role,
        content=content,
        sources=sources
    )
    db.add(msg)
    db.commit()

