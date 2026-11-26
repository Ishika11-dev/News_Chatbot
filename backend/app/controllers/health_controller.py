from typing import Dict, Any
from sqlalchemy.orm import Session

from app.services import health_service


def handle_health_check(db: Session) -> Dict[str, Any]:
    """Handles system health check requests."""
    return health_service.get_health_status(db=db)


def handle_system_stats(db: Session) -> Dict[str, Any]:
    """Handles system analytics and retention stats requests."""
    return health_service.get_system_stats(db=db)

