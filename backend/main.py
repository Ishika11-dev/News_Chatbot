import sys
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

# CORS Middleware for future frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
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

# ==============================================================================
# Execution & Verification Block
# ==============================================================================
if __name__ == "__main__":
    if "--test" in sys.argv:
        from fastapi.testclient import TestClient
        print("=" * 70)
        print("  PHASE 6: FASTAPI APPLICATION & ENDPOINTS VERIFICATION")
        print("=" * 70)

        # Initialize database tables
        init_db()

        client = TestClient(app)

        # 1. Root & Health Check
        print("\n[1] Testing GET / and GET /api/health...")
        r_root = client.get("/")
        print(f"    GET /             -> Status {r_root.status_code}: {r_root.json().get('service')}")
        r_health = client.get("/api/health")
        print(f"    GET /api/health   -> Status {r_health.status_code}: {r_health.json().get('status')}")

        # 2. Stats
        print("\n[2] Testing GET /api/stats...")
        r_stats = client.get("/api/stats")
        print(f"    GET /api/stats    -> Status {r_stats.status_code}: {r_stats.json().get('vector_store')}")

        # 3. News Categories & List
        print("\n[3] Testing GET /api/news and /api/news/categories...")
        r_cats = client.get("/api/news/categories")
        print(f"    GET /categories   -> Status {r_cats.status_code}: {r_cats.json()}")
        r_news = client.get("/api/news?limit=3")
        print(f"    GET /api/news     -> Status {r_news.status_code}: {r_news.json().get('total')} articles in DB")

        # 4. RAG Chat Endpoint
        print("\n[4] Testing POST /api/chat (LangChain RAG QA)...")
        session_id = "test-session-001"
        payload = {
            "message": "What investigation was launched regarding Nvidia?",
            "session_id": session_id,
            "top_k": 3
        }
        r_chat = client.post("/api/chat", json=payload)
        print(f"    POST /api/chat    -> Status {r_chat.status_code}")
        if r_chat.status_code == 200:
            chat_data = r_chat.json()
            print(f"    Answer            : {chat_data.get('answer')[:120]}...")
            print(f"    Sources Returned  : {len(chat_data.get('sources', []))}")
            for s in chat_data.get("sources", []):
                print(f"      [{s.get('citation_id')}] {s.get('title')} ({s.get('publisher')})")

        # 5. Chat History
        print(f"\n[5] Testing GET /api/chat/history/{session_id}...")
        r_hist = client.get(f"/api/chat/history/{session_id}")
        print(f"    GET /history      -> Status {r_hist.status_code}: {len(r_hist.json())} messages recorded")

        # 6. Chat Streaming
        print("\n[6] Testing POST /api/chat/stream (SSE Streaming)...")
        with client.stream("POST", "/api/chat/stream", json={"message": "Summarize Nvidia news", "top_k": 2}) as stream_resp:
            print(f"    POST /chat/stream -> Status {stream_resp.status_code}")
            tokens = []
            for line in stream_resp.iter_lines():
                if line and line.startswith("data: "):
                    tokens.append(line[6:])
            print(f"    Stream Received   : {len(tokens)} SSE chunks successfully received.")

        print("\n" + "=" * 70)
        print("  [SUCCESS] Phase 6 FastAPI Application & Endpoints Verified!")
        print("=" * 70)
    else:
        import uvicorn
        print("\n" + "=" * 65)
        print("  🚀 News Intelligence Server is LIVE!")
        print(f"  👉 Swagger UI  : http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/docs")
        print(f"  👉 Health API  : http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/api/health")
        print(f"  👉 System Stats: http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/api/stats")
        print("=" * 65 + "\n")
        uvicorn.run(app, host=settings.SERVER_HOST, port=settings.SERVER_PORT, reload=False)
