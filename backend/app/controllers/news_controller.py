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


def handle_list_categories() -> List[str]:
    """Handles news category listing requests."""
    return news_service.get_news_categories()

