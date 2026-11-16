import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Project Information
    PROJECT_NAME: str = "AI-Powered News Intelligence Chatbot"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # LLM Provider (Ollama / Gemini)
    LLM_PROVIDER: str = Field(default="ollama", description="LLM Provider: 'ollama' or 'gemini'")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama Base URL")
    OLLAMA_MODEL: str = Field(default="qwen3:4b", description="Ollama Model Name")

    # Gemini AI (Used for Embeddings & optional Gemini LLM)
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-3.8-flash", description="Gemini Chat Model")
    GEMINI_EMBEDDING_MODEL: str = Field(default="gemini-embedding-001", description="Embedding Model")
    EMBEDDING_DIMENSION: int = 3072

    # Vector DB (Qdrant)
    QDRANT_URL: str | None = None
    QDRANT_API_KEY: str | None = None
    QDRANT_STORAGE_PATH: str = str(BASE_DIR / "data" / "qdrant")
    QDRANT_COLLECTION_NAME: str = "news_articles"

    # Relational Database (PostgreSQL required)
    DATABASE_URL: str = "postgresql+psycopg://postgres:Postgres123@localhost:54323/news_db"

    # Ingestion & Retention
    FEEDS_CONFIG_PATH: str = str(BASE_DIR / "feeds.yaml")
    RETENTION_DAYS: int = 30
    INGESTION_INTERVAL_HOURS: int = 12
    CLEANUP_INTERVAL_HOURS: int = 24

    # RAG Settings
    TOP_K_RETRIEVAL: int = 6
    SIMILARITY_THRESHOLD: float = 0.30

settings = Settings()

