from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.database import get_db
from app.db.crud import get_recent_articles
from app.utils.date_utils import get_cutoff_timestamp
from app.config import settings

router = APIRouter(prefix="/api/news", tags=["News"])

@router.get("")
def list_recent_news(
    category: Optional[str] = Query(None, description="Optional category filter"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Returns stored news articles published within the last 30 days."""
    cutoff = get_cutoff_timestamp(retention_days=settings.RETENTION_DAYS)
    articles = get_recent_articles(db, cutoff_timestamp=cutoff, category=category, limit=limit, offset=offset)

    return {
        "total": len(articles),
        "limit": limit,
        "offset": offset,
        "articles": [
            {
                "article_id": a.article_id,
                "title": a.title,
                "summary": a.summary,
                "publisher": a.publisher,
                "category": a.category,
                "published_at": a.published_at.isoformat(),
                "article_url": a.article_url,
                "image_url": a.image_url
            }
            for a in articles
        ]
    }

@router.get("/categories")
def list_categories():
    """Returns active news categories."""
    return [
        "All",
        "Technology",
        "Business",
        "World News",
        "Politics",
        "Science"
    ]

