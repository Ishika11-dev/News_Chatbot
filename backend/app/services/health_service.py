from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.core.langchain_vector_store import get_qdrant_client
from app.db.models import ArticleModel


def _check_postgres(db: Session) -> Dict[str, Any]:
    """Verifies active database connectivity via a lightweight query."""
    try:
        db.execute(text("SELECT 1"))
        return {"connected": True, "error": None}
    except Exception as e:
        return {"connected": False, "error": str(e)}


def _check_qdrant() -> Dict[str, Any]:
    """Verifies active Qdrant vector database connectivity."""
    try:
        client = get_qdrant_client()
        client.get_collections()
        return {"connected": True, "error": None}
    except Exception as e:
        return {"connected": False, "error": str(e)}


def get_health_status(db: Session) -> Dict[str, Any]:
    """Checks Postgres and Qdrant connectivity and returns overall health status."""
    postgres = _check_postgres(db)
    qdrant = _check_qdrant()
    all_connected = postgres["connected"] and qdrant["connected"]

    return {
        "status": "HEALTHY" if all_connected else "DEGRADED",
        "connected": all_connected,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
        "checks": {
            "postgres": postgres,
            "qdrant": qdrant,
        },
    }


def get_system_stats(db: Session) -> Dict[str, Any]:
    """Collects 30-day article counts, Qdrant vector metrics, and model configuration."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_DAYS)).timestamp()
    active_articles = (
        db.query(ArticleModel)
        .filter(ArticleModel.published_timestamp >= cutoff)
        .count()
    )

    qdrant_stats: Dict[str, Any]
    try:
        client = get_qdrant_client()
        info = client.get_collection(settings.QDRANT_COLLECTION_NAME)
        qdrant_stats = {
            "collection": settings.QDRANT_COLLECTION_NAME,
            "status": str(info.status),
            "points_count": info.points_count,
            "vectors_count": getattr(info, "vectors_count", info.points_count),
        }
    except Exception as e:
        qdrant_stats = {"error": str(e)}

    return {
        "active_articles_30d": active_articles,
        "retention_window_days": settings.RETENTION_DAYS,
        "vector_store": qdrant_stats,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": (
            settings.OLLAMA_MODEL
            if settings.LLM_PROVIDER == "ollama"
            else getattr(settings, "GEMINI_MODEL", "qwen3:4b")
        ),
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
    }

