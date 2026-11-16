from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.schemas.chat import ChatRequest, ChatResponse, SourceCitation
from app.core.langchain_rag import LangChainNewsRAG
from app.db.database import get_db
from app.db.crud import save_chat_message
from app.db.models import ChatMessageModel, ChatSessionModel

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])

# Lazy singleton to avoid file locking collisions during module import
_rag_engine: Optional[LangChainNewsRAG] = None

def get_rag_engine() -> LangChainNewsRAG:
    """Returns or lazily initializes the LangChainNewsRAG singleton."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = LangChainNewsRAG()
    return _rag_engine

@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Receives user query, runs 30-day RAG retrieval, and generates grounded answer with citations."""
    session_id = request.session_id or str(uuid.uuid4())
    rag = get_rag_engine()

    # Save user query
    save_chat_message(db, session_id=session_id, role="user", content=request.message)

    result = rag.answer_question(
        question=request.message,
        category=request.category,
        top_k=request.top_k or 5
    )

    # Save assistant answer & citations
    save_chat_message(
        db,
        session_id=session_id,
        role="assistant",
        content=result["answer"],
        sources=result["sources"]
    )

    citations = [
        SourceCitation(
            citation_id=s.get("citation_id"),
            title=s.get("title", ""),
            publisher=s.get("publisher", ""),
            published_at=s.get("published_at", ""),
            url=s.get("url", ""),
            category=s.get("category")
        )
        for s in result["sources"]
    ]

    return ChatResponse(
        answer=result["answer"],
        sources=citations,
        session_id=session_id
    )

@router.post("/stream")
def stream_chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Streams response tokens in real-time via Server-Sent Events (SSE)."""
    session_id = request.session_id or str(uuid.uuid4())
    rag = get_rag_engine()

    # Save user message
    save_chat_message(db, session_id=session_id, role="user", content=request.message)

    return StreamingResponse(
        rag.stream_answer(
            question=request.message,
            category=request.category,
            top_k=request.top_k or 5
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
