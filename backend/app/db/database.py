from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
from app.utils.logger import logger

Base = declarative_base()

def get_engine():
    """Initializes SQLAlchemy engine for PostgreSQL."""
    db_url = settings.DATABASE_URL

    # Ensure psycopg driver is used if generic postgresql:// scheme is passed
    if db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300
    )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes database tables on the required database.
    Strictly fails startup if the database is unavailable (zero silent fallback).
    """
    try:
        # Pre-flight connection test
        with engine.connect() as conn:
            pass
        Base.metadata.create_all(bind=engine)
        logger.info(f"Connected successfully to required database: {engine.url.render_as_string(hide_password=True)}")
    except Exception as e:
        logger.critical(
            f"\n{'='*75}\n"
            f"[FATAL DATABASE ERROR] Failed to connect to required database!\n"
            f"Target URL: {engine.url.render_as_string(hide_password=True)}\n"
            f"Error Details: {e}\n\n"
            f"ACTION REQUIRED:\n"
            f"  1. Ensure your PostgreSQL server is running and accessible.\n"
            f"  2. Check host, port, credentials, and database name in .env (DATABASE_URL).\n"
            f"Startup halted: Automatic fallback to SQLite is disabled for data integrity.\n"
            f"{'='*75}"
        )
        raise RuntimeError(f"Database connection failed: {e}. Application startup aborted.") from e
