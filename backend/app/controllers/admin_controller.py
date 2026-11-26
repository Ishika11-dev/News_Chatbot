from typing import Dict, Any

from app.services import admin_service


def handle_trigger_ingestion() -> Dict[str, Any]:
    """Handles manual news ingestion trigger requests."""
    return admin_service.trigger_ingestion()


def handle_trigger_cleanup() -> Dict[str, Any]:
    """Handles manual 30-day retention cleanup requests."""
    return admin_service.trigger_cleanup()


def handle_list_feeds() -> Dict[str, Any]:
    """Handles requests to list configured RSS feeds."""
    return admin_service.get_configured_feeds()

