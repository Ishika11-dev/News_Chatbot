from typing import Dict, Any

from app.core.scheduler import scheduler_manager


def trigger_ingestion() -> Dict[str, Any]:
    """Manually runs the news ingestion pipeline and returns status metadata."""
    stats = scheduler_manager.run_ingestion_pipeline()
    return {
        "status": "COMPLETED",
        "message": "Manual ingestion finished.",
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

