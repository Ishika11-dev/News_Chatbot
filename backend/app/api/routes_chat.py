from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest, ChatResponse
from app.db.database import get_db
from app.controllers import chat_controller
from app.services.chat_service import get_rag_engine  # noqa: F401 (re-exported for compatibility)

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])

@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Receives user query, runs 30-day RAG retrieval, and generates grounded answer with citations."""
    return chat_controller.handle_chat(db=db, request=request)

@router.post("/stream")
def stream_chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Streams response tokens in real-time via Server-Sent Events (SSE)."""
    return chat_controller.handle_chat_stream(db=db, request=request)

@router.get("/history/{session_id}")
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Retrieves previous messages for a conversation session."""
    return chat_controller.handle_chat_history(db=db, session_id=session_id)

@router.delete("/history/{session_id}")
def delete_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Deletes a conversation session and all of its stored messages."""
    return chat_controller.handle_delete_chat_history(db=db, session_id=session_id)
