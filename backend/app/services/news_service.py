from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.db.crud import get_recent_articles
from app.utils.date_utils import get_cutoff_timestamp

NEWS_CATEGORIES = [
    "All",
    "Technology",
    "Business",
    "World News",
    "Politics",
    "Science",
]


def get_recent_news(
    db: Session,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Fetches and serializes stored news articles within the retention window."""
    cutoff = get_cutoff_timestamp(retention_days=settings.RETENTION_DAYS)
    articles = get_recent_articles(
        db,
        cutoff_timestamp=cutoff,
        category=category,
        limit=limit,
        offset=offset,
    )

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
                "image_url": a.image_url,
            }
            for a in articles
        ],
    }


def get_news_categories() -> List[str]:
    """Returns supported news categories."""
    return list(NEWS_CATEGORIES)

