from typing import Optional, Iterator, List, Dict, Any
import uuid
from sqlalchemy.orm import Session

from app.core.langchain_rag import LangChainNewsRAG
from app.db.crud import save_chat_message
from app.db.models import ChatMessageModel
from app.schemas.chat import ChatRequest, ChatResponse, SourceCitation

# Lazy singleton to avoid file locking collisions during module import
_rag_engine: Optional[LangChainNewsRAG] = None


def get_rag_engine() -> LangChainNewsRAG:
    """Returns or lazily initializes the LangChainNewsRAG singleton."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = LangChainNewsRAG()
    return _rag_engine


def process_chat_message(db: Session, request: ChatRequest) -> ChatResponse:
    """Persists the user query, runs RAG retrieval/generation, and stores the response."""
    session_id = request.session_id or str(uuid.uuid4())
    rag = get_rag_engine()

    save_chat_message(db, session_id=session_id, role="user", content=request.message)

    try:
        result = rag.answer_question(
            question=request.message,
            category=request.category,
            top_k=request.top_k or 5,
        )
    except Exception as e:
        result = {
            "answer": f"I encountered an error retrieving news: {e}",
            "sources": [],
        }

    save_chat_message(
        db,
        session_id=session_id,
        role="assistant",
        content=result["answer"],
        sources=result["sources"],
    )

    citations = [
        SourceCitation(
            citation_id=s.get("citation_id"),
            title=s.get("title", ""),
            publisher=s.get("publisher", ""),
            published_at=s.get("published_at", ""),
            url=s.get("url", ""),
            category=s.get("category"),
        )
        for s in result["sources"]
    ]

    return ChatResponse(
        answer=result["answer"],
        sources=citations,
        session_id=session_id,
    )


def stream_chat_message(db: Session, request: ChatRequest) -> Iterator[str]:
    """Persists the user query and returns an SSE token stream from the RAG engine."""
    session_id = request.session_id or str(uuid.uuid4())
    rag = get_rag_engine()

    save_chat_message(db, session_id=session_id, role="user", content=request.message)

    return rag.stream_answer(
        question=request.message,
        category=request.category,
        top_k=request.top_k or 5,
    )


def get_session_history(db: Session, session_id: str) -> List[Dict[str, Any]]:
    """Retrieves chronologically ordered chat messages for a session."""
    messages = (
        db.query(ChatMessageModel)
        .filter(ChatMessageModel.session_id == session_id)
        .order_by(ChatMessageModel.created_at.asc())
        .all()
    )

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "sources": m.sources,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]

