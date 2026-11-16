from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.db.database import get_db
from app.db.models import ArticleModel
from app.core.langchain_vector_store import get_qdrant_client
from app.config import settings

router = APIRouter(tags=["Health & System"])

@router.get("/api/health")
def health_check():
    """System status check."""
    return {
        "status": "HEALTHY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME
    }

@router.get("/api/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """Provides system analytics: vector counts, active articles, and 30-day retention status."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_DAYS)).timestamp()
    active_articles = db.query(ArticleModel).filter(
        ArticleModel.published_timestamp >= cutoff
    ).count()

    qdrant_stats = {}
    try:
        client = get_qdrant_client()
        info = client.get_collection(settings.QDRANT_COLLECTION_NAME)
        qdrant_stats = {
            "collection": settings.QDRANT_COLLECTION_NAME,
            "status": str(info.status),
            "points_count": info.points_count,
            "vectors_count": getattr(info, "vectors_count", info.points_count)
        }
    except Exception as e:
        qdrant_stats = {"error": str(e)}

    return {
        "active_articles_30d": active_articles,
        "retention_window_days": settings.RETENTION_DAYS,
        "vector_store": qdrant_stats,
        "gemini_model": settings.GEMINI_MODEL,
        "embedding_model": settings.GEMINI_EMBEDDING_MODEL
    }
