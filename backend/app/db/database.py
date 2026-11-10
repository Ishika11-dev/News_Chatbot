from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path
from app.config import settings
from app.utils.logger import logger

db_url = settings.DATABASE_URL

# If sqlite, ensure local directory exists
if db_url.startswith("sqlite"):
    db_path = db_url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    # PostgreSQL connection with pool recycle
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=300)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes tables in the relational database."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Relational database tables verified/created successfully.")
    except Exception as e:
        logger.warning(f"Could not connect to configured DB ({e}). Creating fallback SQLite.")
        fallback_engine = create_engine("sqlite:///./data/news.db", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=fallback_engine)

