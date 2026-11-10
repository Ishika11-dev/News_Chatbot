from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import uuid

from app.schemas.chat import ChatRequest, ChatResponse
from app.core.rag_engine import NewsRAGEngine
from app.db.database import get_db
from app.db.crud import save_chat_message
from app.db.models import ChatMessageModel, ChatSessionModel

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])
rag_engine = NewsRAGEngine()

@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Receives user query, runs 30-day RAG retrieval, and generates grounded answer with citations."""
    session_id = request.session_id or str(uuid.uuid4())

    # Save user query
    save_chat_message(db, session_id=session_id, role="user", content=request.message)

    response = rag_engine.answer_query(
        query=request.message,
        category=request.category,
        session_id=session_id,
        top_k=request.top_k or 6
    )

    # Save assistant answer
    sources_data = [s.model_dump() for s in response.sources]
    save_chat_message(
        db,
        session_id=session_id,
        role="assistant",
        content=response.answer,
        sources=sources_data
    )

    return response

@router.post("/stream")
def stream_chat_endpoint(request: ChatRequest):
    """Streams response tokens in real-time via Server-Sent Events (SSE)."""
    session_id = request.session_id or str(uuid.uuid4())

    return StreamingResponse(
        rag_engine.stream_answer(
            query=request.message,
            category=request.category,
            session_id=session_id,
            top_k=request.top_k or 6
        ),
        media_type="text/event-stream"
    )

@router.get("/history/{session_id}")
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Retrieves previous messages for a conversation session."""
    messages = db.query(ChatMessageModel).filter(
        ChatMessageModel.session_id == session_id
    ).order_by(ChatMessageModel.created_at.asc()).all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "sources": m.sources,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]

