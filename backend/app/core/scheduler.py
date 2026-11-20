"""
News Scheduler & 30-Day Retention Manager (Phase 5)
--------------------------------------------------
Automates periodic news ingestion using LangChain Document pipelines
and enforces strict 30-day retention cleanup across Qdrant and SQLite/PostgreSQL.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Set, Dict, Any
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from qdrant_client.http import models as qmodels

from app.config import settings
from app.ingestion import NewsIngestionPipeline
from app.core.langchain_vector_store import get_vector_store, get_qdrant_client, add_documents_to_qdrant
from app.db.database import SessionLocal, init_db
from app.db.crud import (
    get_existing_article_ids,
    save_articles,
    delete_expired_articles,
    log_ingestion
)
from app.schemas.news import CleanedArticle, IngestionStats
from app.utils.logger import logger


class NewsSchedulerManager:
    """Coordinates automated news ingestion and 30-day data retention cleanup."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.ingestor = NewsIngestionPipeline(
            feeds_config_path=settings.FEEDS_CONFIG_PATH,
            retention_days=settings.RETENTION_DAYS
        )

    def run_ingestion_pipeline(self, max_articles: Optional[int] = None) -> IngestionStats:
        """
        Executes full news extraction, deduplication, LangChain chunking,
        vector storage in Qdrant, and metadata persistence in the relational DB.
        """
        start_time = time.time()
        logger.info("--- Starting Scheduled LangChain News Ingestion Pipeline ---")

        stats = IngestionStats(total_feeds=len(self.ingestor.load_feed_configs()))
        db = SessionLocal()

        try:
            # 1. Retrieve existing article IDs to prevent duplicate embedding
            existing_ids: Set[str] = get_existing_article_ids(db)

            # 2. Extract and clean articles strictly within 30-day window
            parent_docs = self.ingestor.fetch_articles_as_documents(seen_ids=existing_ids)
            stats.total_fetched = len(parent_docs)

            if not parent_docs:
                logger.info("No new articles to ingest.")
                stats.duration_seconds = round(time.time() - start_time, 2)
                log_ingestion(db, stats, status="SUCCESS")
                return stats

            if max_articles and len(parent_docs) > max_articles:
                parent_docs = parent_docs[:max_articles]

            # 3. Split into LangChain Document chunks
            chunked_docs = self.ingestor.chunk_documents(parent_docs)
            stats.total_chunks_created = len(chunked_docs)

            logger.info(f"Split {len(parent_docs)} articles into {len(chunked_docs)} LangChain chunks.")

            # 4. Embed and store chunks in Qdrant Vector Store
            try:
                stored_count = add_documents_to_qdrant(chunked_docs)
                stats.total_chunks_stored = stored_count
            except Exception as e:
                logger.error(f"Vector storage failed: {e}")
                stats.total_chunks_stored = 0
                stats.status = "FAILED"
                stats.error_message = str(e)
                stats.duration_seconds = round(time.time() - start_time, 2)
                db.rollback()
                log_ingestion(db, stats, status="FAILED")
                return stats

            # Transactional Safety Guard: If chunks were generated but zero stored, abort before writing to SQL
            if chunked_docs and stored_count == 0:
                logger.error("Abort: Zero chunks stored in Qdrant. Skipping database persistence to avoid orphaned records.")
                stats.status = "FAILED"
                stats.error_message = "Zero chunks stored in Qdrant"
                stats.duration_seconds = round(time.time() - start_time, 2)
                db.rollback()
                log_ingestion(db, stats, status="FAILED")
                return stats

            # 5. Save parent article records in relational DB only if chunks stored
            cleaned_articles: List[CleanedArticle] = []
            for doc in parent_docs:
                meta = doc.metadata
                try:
                    pub_dt = datetime.fromisoformat(meta["published_at"])
                except Exception:
                    pub_dt = datetime.now(timezone.utc)

                cleaned_articles.append(
                    CleanedArticle(
                        article_id=meta["article_id"],
                        title=meta["title"],
                        content=doc.page_content,
                        summary=doc.page_content[:300],
                        publisher=meta["publisher"],
                        published_at=pub_dt,
                        published_timestamp=float(meta["published_timestamp"]),
                        category=meta["category"],
                        article_url=meta["url"]
                    )
                )

            saved = save_articles(db, cleaned_articles)
            stats.new_articles_ingested = saved
            stats.duration_seconds = round(time.time() - start_time, 2)

            # Distinguish Partial vs Full Success
            if stored_count < len(chunked_docs):
                stats.status = "PARTIAL_FAILURE"
                stats.error_message = f"Stored {stored_count}/{len(chunked_docs)} chunks in Qdrant."
                log_ingestion(db, stats, status="PARTIAL_FAILURE")
                logger.warning(f"Ingestion finished with PARTIAL_FAILURE: {saved} articles saved, but only {stored_count}/{len(chunked_docs)} chunks stored in Qdrant.")
            else:
                stats.status = "SUCCESS"
                log_ingestion(db, stats, status="SUCCESS")
                logger.info(f"Ingestion finished successfully: {saved} articles ({stored_count} chunks) saved in {stats.duration_seconds}s.")

            return stats

        except Exception as e:
            logger.error(f"Error during ingestion pipeline: {e}")
            stats.status = "FAILED"
            stats.error_message = str(e)
            stats.duration_seconds = round(time.time() - start_time, 2)
            try:
                db.rollback()
                log_ingestion(db, stats, status="FAILED")
            except Exception:
                pass
            return stats
        finally:
            db.close()

    def run_cleanup_pipeline(self) -> Dict[str, Any]:
        """
        Enforces strict 30-day retention:
        Deletes vector points from Qdrant and rows from relational DB older than 30 days.
        """
        logger.info("--- Starting 30-Day Retention Cleanup Pipeline ---")
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_DAYS)
        cutoff_timestamp = cutoff_date.timestamp()

        # 1. Purge expired vectors from Qdrant
        qdrant_status = "SUCCESS"
        try:
            client = get_qdrant_client()
            client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="metadata.published_timestamp",
                                range=qmodels.Range(lt=cutoff_timestamp)
                            )
                        ]
                    )
                )
            )
            logger.info(f"Qdrant purge completed for articles before {cutoff_date.isoformat()}.")
        except Exception as e:
            logger.warning(f"Notice while purging Qdrant vectors: {e}")
            qdrant_status = f"NOTICE: {e}"

        # 2. Purge expired articles from relational database
        db = SessionLocal()
        deleted_db = 0
        try:
            deleted_db = delete_expired_articles(db, cutoff_timestamp=cutoff_timestamp)
            logger.info(f"Purged {deleted_db} expired articles from database.")
        except Exception as e:
            logger.error(f"Error cleaning relational DB: {e}")
        finally:
            db.close()

        return {
            "cutoff_timestamp": cutoff_timestamp,
            "cutoff_date": cutoff_date.isoformat(),
            "deleted_db_articles": deleted_db,
            "qdrant_status": qdrant_status
        }

    def start_scheduler(self):
        """Starts background scheduled tasks for ingestion and retention purge."""
        # 1. Recurring Ingestion
        self.scheduler.add_job(
            func=self.run_ingestion_pipeline,
            trigger=IntervalTrigger(hours=settings.INGESTION_INTERVAL_HOURS),
            id="recurring_news_ingestion",
            name="Periodic News Ingestion Job",
            replace_existing=True
        )

        # 2. Daily Retention Cleanup at 00:00 UTC
        self.scheduler.add_job(
            func=self.run_cleanup_pipeline,
            trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
            id="daily_retention_cleanup",
            name="Daily 30-Day Retention Purge Job",
            replace_existing=True
        )

        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("News scheduler started successfully.")

    def shutdown(self):
        """Gracefully shuts down the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("News scheduler stopped.")


# Module singleton
scheduler_manager = NewsSchedulerManager()


# ==============================================================================
# Standalone Manual Test Block (Runs only when executed directly)
# ==============================================================================
if __name__ == "__main__":
    import sys

    # Ensure backend directory is in path
    backend_dir = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(backend_dir))

    print("=" * 70)
    print("  PHASE 5: SCHEDULER & 30-DAY RETENTION TEST")
    print("=" * 70)

    # Initialize tables
    print("\n[1] Initializing database...")
    init_db()

    manager = NewsSchedulerManager()

    # 1. Test 30-Day Cleanup Pipeline
    print("\n[2] Testing 30-Day Retention Cleanup Pipeline...")
    cleanup_result = manager.run_cleanup_pipeline()
    print(f"    Cutoff Date         : {cleanup_result['cutoff_date']}")
    print(f"    Purged DB Articles  : {cleanup_result['deleted_db_articles']}")
    print(f"    Qdrant Purge Status : {cleanup_result['qdrant_status']}")

    # 2. Test Ingestion Pipeline with a small batch
    print("\n[3] Testing Ingestion Pipeline (Fresh sync test)...")
    stats = manager.run_ingestion_pipeline(max_articles=5)
    print(f"    Feeds Scanned        : {stats.total_feeds}")
    print(f"    New Articles Ingested: {stats.new_articles_ingested}")
    print(f"    Chunks Created       : {stats.total_chunks_created}")
    print(f"    Chunks Stored        : {stats.total_chunks_stored}")
    print(f"    Pipeline Status      : {stats.status}")
    print(f"    Duration             : {stats.duration_seconds}s")
    if stats.error_message:
        print(f"    Error Reason         : {stats.error_message}")

    print("\n" + "=" * 70)
    if stats.status == "FAILED":
        print("  [FAILED] Pipeline failed at Qdrant vector storage stage.")
    elif stats.status == "PARTIAL_FAILURE":
        print("  [WARNING] Pipeline finished with partial storage.")
    else:
        print("  [SUCCESS] Phase 5 Scheduler & Retention pipeline verified!")
    print("=" * 70)
