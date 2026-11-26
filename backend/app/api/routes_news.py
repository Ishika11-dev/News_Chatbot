from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.controllers import news_controller

router = APIRouter(prefix="/api/news", tags=["News"])

@router.get("")
def list_recent_news(
    category: Optional[str] = Query(None, description="Optional category filter"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Returns stored news articles published within the last 30 days."""
    return news_controller.handle_list_recent_news(
        db=db,
        category=category,
        limit=limit,
        offset=offset,
    )

@router.get("/categories")
def list_categories():
    """Returns active news categories."""
    return news_controller.handle_list_categories()

