from typing import Dict, Any, List, Optional, Union

from app.services import admin_service


def handle_trigger_ingestion(
    categories: Optional[Union[str, List[str]]] = None,
) -> Dict[str, Any]:
    """Handles manual news ingestion trigger requests."""
    return admin_service.trigger_ingestion(categories=categories)


def handle_trigger_cleanup() -> Dict[str, Any]:
    """Handles manual 30-day retention cleanup requests."""
    return admin_service.trigger_cleanup()


def handle_list_feeds() -> Dict[str, Any]:
    """Handles requests to list configured RSS feeds."""
    return admin_service.get_configured_feeds()

