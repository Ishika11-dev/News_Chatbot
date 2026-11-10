from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SourceCitation(BaseModel):
    title: str
    publisher: str
    published_at: str
    url: str
    category: Optional[str] = None
    score: Optional[float] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000, description="User question or query")
    session_id: Optional[str] = Field(None, description="Optional conversation session ID")
    category: Optional[str] = Field(None, description="Optional news category filter")
    top_k: Optional[int] = Field(6, ge=1, le=15, description="Number of context chunks to retrieve")

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation] = []
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

