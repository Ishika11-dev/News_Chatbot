from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List

class FeedConfig(BaseModel):
    name: str
    url: str
    category: str
    publisher: str
    language: str = "en"

class RawArticle(BaseModel):
    title: str
    link: str
    summary: Optional[str] = None
    content: Optional[str] = None
    published_raw: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    publisher: str
    category: str

class CleanedArticle(BaseModel):
    article_id: str = Field(description="Unique SHA-256 hash identifier")
    title: str
    content: str
    summary: str
    publisher: str
    published_at: datetime
    published_timestamp: float = Field(description="UTC Epoch seconds for fast numeric range filter")
    category: str
    article_url: str
    author: Optional[str] = None
    image_url: Optional[str] = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ArticleChunk(BaseModel):
    chunk_id: str
    article_id: str
    chunk_index: int
    text: str
    title: str
    publisher: str
    published_at: str  # ISO 8601 string
    published_timestamp: float
    category: str
    article_url: str
    image_url: Optional[str] = None

class IngestionStats(BaseModel):
    total_feeds: int = 0
    total_fetched: int = 0
    new_articles_ingested: int = 0
    duplicates_skipped: int = 0
    failed_feeds: List[str] = []
    duration_seconds: float = 0.0

