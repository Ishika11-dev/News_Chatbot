from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path
from app.config import settings
from app.utils.logger import logger

Base = declarative_base()

def _create_database_engine():
    """Initializes database engine with automatic fallback to local SQLite if Postgres is unavailable."""
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return create_engine(db_url, connect_args={"check_same_thread": False})

    try:
        pg_engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=300)
        with pg_engine.connect() as conn:
            pass
        return pg_engine
    except Exception as e:
        logger.warning(f"Could not connect to configured DB ({e}). Falling back to local SQLite.")
        Path("data").mkdir(parents=True, exist_ok=True)
        return create_engine("sqlite:///./data/news.db", connect_args={"check_same_thread": False})

engine = _create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes tables in the relational database."""
    global engine, SessionLocal
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Relational database tables verified/created successfully.")
    except Exception as e:
        logger.warning(f"Error initializing DB ({e}). Binding fallback SQLite.")
        Path("data").mkdir(parents=True, exist_ok=True)
        engine = create_engine("sqlite:///./data/news.db", connect_args={"check_same_thread": False})
        SessionLocal.configure(bind=engine)
        Base.metadata.create_all(bind=engine)
