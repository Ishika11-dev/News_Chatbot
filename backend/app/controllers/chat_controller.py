from typing import List, Dict, Any
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service


def handle_chat(db: Session, request: ChatRequest) -> ChatResponse:
    """Handles standard RAG chat requests."""
    return chat_service.process_chat_message(db=db, request=request)


def handle_chat_stream(db: Session, request: ChatRequest) -> StreamingResponse:
    """Handles SSE streaming chat requests."""
    token_stream = chat_service.stream_chat_message(db=db, request=request)
    return StreamingResponse(token_stream, media_type="text/event-stream")


def handle_chat_history(db: Session, session_id: str) -> List[Dict[str, Any]]:
    """Handles chat history retrieval for a given session."""
    return chat_service.get_session_history(db=db, session_id=session_id)


def handle_delete_chat_history(db: Session, session_id: str) -> Dict[str, Any]:
    """Handles deletion of a chat session and its history."""
    return chat_service.delete_session_history(db=db, session_id=session_id)

