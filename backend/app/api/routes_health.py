from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.database import get_db
from app.db.models import ArticleModel
from app.core.vector_store import QdrantNewsStore
from app.utils.date_utils import get_cutoff_timestamp, format_iso_utc
from app.config import settings

router = APIRouter(tags=["Health & System"])
vector_store = QdrantNewsStore()

@router.get("/api/health")
def health_check():
    """System status check."""
    return {
        "status": "HEALTHY",
        "timestamp": format_iso_utc(datetime.now(timezone.utc)),
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME
    }

@router.get("/api/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """Provides system analytics: vector counts, active articles, and 30-day retention status."""
    cutoff = get_cutoff_timestamp(retention_days=settings.RETENTION_DAYS)
    active_articles = db.query(ArticleModel).filter(
        ArticleModel.published_timestamp >= cutoff
    ).count()

    qdrant_stats = vector_store.get_stats()

    return {
        "active_articles_30d": active_articles,
        "retention_window_days": settings.RETENTION_DAYS,
        "vector_store": qdrant_stats,
        "gemini_model": settings.GEMINI_MODEL,
        "embedding_model": settings.GEMINI_EMBEDDING_MODEL
    }

