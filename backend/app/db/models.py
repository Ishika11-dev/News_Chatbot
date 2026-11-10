from sqlalchemy import Column, String, Text, Float, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base

class ArticleModel(Base):
    __tablename__ = "articles"

    article_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    publisher = Column(String(128), index=True, nullable=False)
    published_at = Column(DateTime, nullable=False, index=True)
    published_timestamp = Column(Float, nullable=False, index=True)
    category = Column(String(64), index=True, nullable=False)
    article_url = Column(String(1024), nullable=False)
    author = Column(String(256), nullable=True)
    image_url = Column(String(1024), nullable=True)
    ingested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_expired = Column(Boolean, default=False, index=True)

class IngestionLogModel(Base):
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_feeds = Column(Integer, default=0)
    total_fetched = Column(Integer, default=0)
    new_articles_ingested = Column(Integer, default=0)
    duplicates_skipped = Column(Integer, default=0)
    status = Column(String(32), default="SUCCESS")
    failed_feeds = Column(Text, nullable=True)
    duration_seconds = Column(Float, default=0.0)

class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(256), default="New Chat")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    messages = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan")

class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.session_id"), index=True)
    role = Column(String(16), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ChatSessionModel", back_populates="messages")

