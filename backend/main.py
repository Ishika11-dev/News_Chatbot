from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.db.database import init_db
from app.core.scheduler import scheduler_manager
from app.api import routes_chat, routes_news, routes_admin, routes_health
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown lifecycle."""
    logger.info("Initializing Database...")
    init_db()

    logger.info("Starting background scheduler...")
    scheduler_manager.start_scheduler()

    yield

    logger.info("Shutting down background scheduler...")
    scheduler_manager.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Continuously updated, RAG-powered news intelligence assistant with 30-day retention.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(routes_chat.router)
app.include_router(routes_news.router)
app.include_router(routes_admin.router)
app.include_router(routes_health.router)

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

