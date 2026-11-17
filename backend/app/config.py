from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR.parent / ".env"), str(BASE_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application
    PROJECT_NAME: str = "AI-Powered News Intelligence Chatbot"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000

    # Secrets & Connection Links (loaded strictly from .env)
    DATABASE_URL: str = ""
    GEMINI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = ""
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""

    # Models & Providers (overridable via .env)
    LLM_PROVIDER: str = "ollama"
    OLLAMA_MODEL: str = "qwen3:4b"
    GEMINI_MODEL: str = "gemini-3.8-flash"
    EMBEDDING_PROVIDER: str = "huggingface"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384

    # Storage Paths
    QDRANT_STORAGE_PATH: str = str(BASE_DIR / "data" / "qdrant")
    QDRANT_COLLECTION_NAME: str = "news_articles"
    FEEDS_CONFIG_PATH: str = str(BASE_DIR / "feeds.yaml")

    # Ingestion & Retention Rules
    RETENTION_DAYS: int = 30
    INGESTION_INTERVAL_HOURS: int = 12
    CLEANUP_INTERVAL_HOURS: int = 24
    TOP_K_RETRIEVAL: int = 6
    SIMILARITY_THRESHOLD: float = 0.35

settings = Settings()
