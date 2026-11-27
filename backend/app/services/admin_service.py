from typing import Dict, Any, List, Optional, Union

from app.core.scheduler import scheduler_manager


def _normalize_categories(
    categories: Optional[Union[str, List[str]]],
) -> Optional[List[str]]:
    """Normalizes a single/comma-separated string or list of category names."""
    if not categories:
        return None
    items = [categories] if isinstance(categories, str) else categories
    parsed: List[str] = []
    for item in items:
        for part in item.split(","):
            cleaned = part.strip()
            if cleaned:
                parsed.append(cleaned)
    return parsed or None


def trigger_ingestion(
    categories: Optional[Union[str, List[str]]] = None,
) -> Dict[str, Any]:
    """Manually runs the news ingestion pipeline (optionally scoped to categories)."""
    normalized = _normalize_categories(categories)
    stats = scheduler_manager.run_ingestion_pipeline(categories=normalized)
    return {
        "status": "COMPLETED",
        "message": (
            f"Manual ingestion finished for categories: {', '.join(normalized)}."
            if normalized
            else "Manual ingestion finished."
        ),
        "stats": stats,
    }


def trigger_cleanup() -> Dict[str, Any]:
    """Manually runs the 30-day retention cleanup routine and returns results."""
    result = scheduler_manager.run_cleanup_pipeline()
    return {
        "status": "COMPLETED",
        "message": "30-day retention cleanup finished.",
        "result": result,
    }


def get_configured_feeds() -> Dict[str, Any]:
    """Returns the RSS feeds currently configured in feeds.yaml."""
    feeds = scheduler_manager.ingestor.load_feed_configs()
    return {
        "total_feeds": len(feeds),
        "feeds": feeds,
    }

