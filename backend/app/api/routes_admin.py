from fastapi import APIRouter
from app.core.scheduler import scheduler_manager

router = APIRouter(prefix="/api/admin", tags=["Admin & Control"])

@router.post("/trigger-ingest")
def trigger_manual_ingestion():
    """Manually triggers the news ingestion pipeline."""
    stats = scheduler_manager.run_ingestion_pipeline()
    return {
        "status": "COMPLETED",
        "message": "Manual ingestion finished.",
        "stats": stats
    }

@router.post("/trigger-cleanup")
def trigger_manual_cleanup():
    """Manually triggers the 30-day retention cleanup routine."""
    result = scheduler_manager.run_cleanup_pipeline()
    return {
        "status": "COMPLETED",
        "message": "30-day retention cleanup finished.",
        "result": result
    }

@router.get("/feeds")
def list_configured_feeds():
    """Returns the list of RSS feeds currently configured in feeds.yaml."""
    feeds = scheduler_manager.ingestor.load_feed_configs()
    return {
        "total_feeds": len(feeds),
        "feeds": feeds
    }
