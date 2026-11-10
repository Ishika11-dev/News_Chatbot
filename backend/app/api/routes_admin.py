from fastapi import APIRouter, BackgroundTasks
from app.core.scheduler import scheduler_manager
from app.core.rss_parser import RSSParser

router = APIRouter(prefix="/api/admin", tags=["Admin & Control"])

@router.post("/trigger-ingest")
def trigger_manual_ingestion(background_tasks: BackgroundTasks):
    """Manually triggers the news ingestion pipeline."""
    # Execute asynchronously or directly
    stats = scheduler_manager.run_ingestion_pipeline()
    return {
        "status": "COMPLETED",
        "message": "Manual ingestion finished.",
        "stats": stats
    }

@router.post("/trigger-cleanup")
def trigger_manual_cleanup():
    """Manually triggers the 30-day retention cleanup routine."""
    deleted_count = scheduler_manager.run_cleanup_pipeline()
    return {
        "status": "COMPLETED",
        "message": "30-day retention cleanup finished.",
        "purged_records": deleted_count
    }

@router.get("/feeds")
def list_configured_feeds():
    """Returns the list of RSS feeds currently configured in feeds.yaml."""
    parser = RSSParser()
    return {
        "total_feeds": len(parser.feeds),
        "feeds": [f.model_dump() for f in parser.feeds]
    }

