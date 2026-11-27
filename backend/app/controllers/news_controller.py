from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.services import news_service


def handle_list_recent_news(
    db: Session,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Handles paginated recent news listing requests."""
    return news_service.get_recent_news(
        db=db,
        category=category,
        limit=limit,
        offset=offset,
    )


def handle_list_trending_news(
    db: Session,
    page: int = 1,
    page_size: int = 8,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """Handles paginated trending news listing requests."""
    return news_service.get_trending_news(
        db=db,
        page=page,
        page_size=page_size,
        category=category,
        search=search,
    )


def handle_list_categories() -> List[str]:
    """Handles news category listing requests."""
    return news_service.get_news_categories()

