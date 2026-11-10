import time
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.core.rss_parser import RSSParser
from app.core.deduplicator import ArticleDeduplicator
from app.core.chunker import ArticleChunker
from app.core.embeddings import GeminiEmbedder
from app.core.vector_store import QdrantNewsStore
from app.db.database import SessionLocal
from app.db.crud import get_existing_article_ids, save_articles, log_ingestion, delete_expired_articles
from app.schemas.news import IngestionStats
from app.utils.date_utils import get_cutoff_timestamp
from app.utils.logger import logger

class NewsSchedulerManager:
    """Coordinates automated news ingestion and 30-day data retention cleanup."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.rss_parser = RSSParser()
        self.chunker = ArticleChunker()
        self.embedder = GeminiEmbedder()
        self.vector_store = QdrantNewsStore()

    def run_ingestion_pipeline(self) -> IngestionStats:
        """Executes full news extraction, deduplication, embedding, and vector storage."""
        start_time = time.time()
        logger.info("--- Starting Scheduled News Ingestion Pipeline ---")

        stats = IngestionStats(total_feeds=len(self.rss_parser.feeds))
        db = SessionLocal()

        try:
            # 1. Initialize deduplicator with existing IDs from DB
            existing_ids = get_existing_article_ids(db)
            dedup = ArticleDeduplicator()
            dedup.load_existing_ids(existing_ids)

            # 2. Extract and clean articles across all configured feeds
            new_articles = self.rss_parser.fetch_all_feeds(deduplicator=dedup)
            stats.total_fetched = len(new_articles)

            if not new_articles:
                logger.info("No new articles to ingest.")
                stats.duration_seconds = round(time.time() - start_time, 2)
                log_ingestion(db, stats, status="SUCCESS")
                return stats

            # 3. Chunk articles
            chunks = self.chunker.chunk_articles(new_articles)
            logger.info(f"Generated {len(chunks)} text chunks from {len(new_articles)} articles.")

            # 4. Generate embeddings
            chunk_texts = [f"{c.title}. {c.text}" for c in chunks]
            vectors = self.embedder.embed_batch(chunk_texts, task_type="RETRIEVAL_DOCUMENT")

            # 5. Store in Qdrant
            upserted = self.vector_store.upsert_chunks(chunks, vectors)

            # 6. Save article metadata in relational DB
            saved = save_articles(db, new_articles)
            stats.new_articles_ingested = saved
            stats.duration_seconds = round(time.time() - start_time, 2)

            log_ingestion(db, stats, status="SUCCESS")
            logger.info(f"Ingestion finished: {saved} new articles saved in {stats.duration_seconds}s.")
            return stats

        except Exception as e:
            logger.error(f"Error during ingestion pipeline: {e}")
            stats.duration_seconds = round(time.time() - start_time, 2)
            log_ingestion(db, stats, status="FAILED")
            return stats
        finally:
            db.close()

    def run_cleanup_pipeline(self) -> int:
        """Purges news and vector embeddings older than 30 days."""
        logger.info("--- Starting 30-Day Retention Cleanup Pipeline ---")
        cutoff = get_cutoff_timestamp(retention_days=settings.RETENTION_DAYS)

        # 1. Clean Qdrant vectors
        self.vector_store.delete_expired_articles(cutoff_timestamp=cutoff)

        # 2. Clean Relational DB records
        db = SessionLocal()
        try:
            deleted_db = delete_expired_articles(db, cutoff_timestamp=cutoff)
            logger.info(f"Purged {deleted_db} expired articles from database.")
            return deleted_db
        except Exception as e:
            logger.error(f"Error cleaning relational DB: {e}")
            return 0
        finally:
            db.close()

    def start_scheduler(self):
        """Starts recurring background jobs for ingestion and cleanup."""
        # Recurring Ingestion
        self.scheduler.add_job(
            func=self.run_ingestion_pipeline,
            trigger=IntervalTrigger(hours=settings.INGESTION_INTERVAL_HOURS),
            id="recurring_news_ingestion",
            name="Periodic News Ingestion Job",
            replace_existing=True
        )

        # Daily Retention Cleanup at 00:00 UTC
        self.scheduler.add_job(
            func=self.run_cleanup_pipeline,
            trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
            id="daily_retention_cleanup",
            name="Daily 30-Day Retention Purge Job",
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("APScheduler initialized and running background jobs.")

    def shutdown(self):
        """Gracefully stops the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("APScheduler stopped.")

scheduler_manager = NewsSchedulerManager()

