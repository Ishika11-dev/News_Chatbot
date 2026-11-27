from math import ceil
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.db.crud import get_recent_articles, get_recent_articles_paginated
from app.ingestion.feed_fetcher import FeedFetcher
from app.utils.date_utils import get_cutoff_timestamp

NEWS_CATEGORIES = [
    "All",
    "Technology",
    "Business",
    "World News",
    "Politics",
    "Science",
    "Sports",
    "Entertainment",
]


def _serialize_article(article: Any) -> Dict[str, Any]:
    """Serializes an ArticleModel row into the API response dictionary."""
    return {
        "article_id": article.article_id,
        "title": article.title,
        "summary": article.summary,
        "publisher": article.publisher,
        "category": article.category,
        "published_at": article.published_at.isoformat(),
        "article_url": article.article_url,
        "image_url": article.image_url,
    }


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
        "articles": [_serialize_article(a) for a in articles],
    }


def get_trending_news(
    db: Session,
    page: int = 1,
    page_size: int = 8,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetches paginated recent news articles (default 8 per page) within the retention window."""
    cutoff = get_cutoff_timestamp(retention_days=settings.RETENTION_DAYS)
    articles, total_items = get_recent_articles_paginated(
        db=db,
        cutoff_timestamp=cutoff,
        page=page,
        page_size=page_size,
        category=category,
        search=search,
    )
    total_pages = ceil(total_items / page_size) if total_items > 0 else 0

    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1 and total_pages > 0,
        "articles": [_serialize_article(a) for a in articles],
    }


def get_news_categories() -> List[str]:
    """Returns supported news categories derived from feeds.yaml (with fallback)."""
    feeds = FeedFetcher(config_path=settings.FEEDS_CONFIG_PATH).load_feed_configs()
    if not feeds:
        return list(NEWS_CATEGORIES)

    categories: List[str] = ["All"]
    for feed in feeds:
        cat = (feed.get("category") or "").strip()
        if cat and cat not in categories:
            categories.append(cat)

    return categories if len(categories) > 1 else list(NEWS_CATEGORIES)

