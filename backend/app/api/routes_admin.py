from fastapi import APIRouter
from app.controllers import admin_controller

router = APIRouter(prefix="/api/admin", tags=["Admin & Control"])

@router.post("/trigger-ingest")
def trigger_manual_ingestion():
    """Manually triggers the news ingestion pipeline."""
    return admin_controller.handle_trigger_ingestion()

@router.post("/trigger-cleanup")
def trigger_manual_cleanup():
    """Manually triggers the 30-day retention cleanup routine."""
    return admin_controller.handle_trigger_cleanup()

@router.get("/feeds")
def list_configured_feeds():
    """Returns the list of RSS feeds currently configured in feeds.yaml."""
    return admin_controller.handle_list_feeds()
