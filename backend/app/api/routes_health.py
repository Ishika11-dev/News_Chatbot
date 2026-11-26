from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.controllers import health_controller

router = APIRouter(tags=["Health & System"])

@router.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Checks PostgreSQL and Qdrant connectivity and returns system status."""
    return health_controller.handle_health_check(db=db)

@router.get("/api/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """Provides system analytics: vector counts, active articles, and 30-day retention status."""
    return health_controller.handle_system_stats(db=db)
