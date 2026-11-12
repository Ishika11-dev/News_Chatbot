import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.schemas.news import ArticleChunk
from app.utils.logger import logger

class QdrantNewsStore:
    """Manages Qdrant vector storage, indexing, 30-day filtered queries, and expiration purge."""

    _instance = None
    NAMESPACE_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(QdrantNewsStore, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.client = self._init_client()
        self._ensure_collection_and_indexes()
        self._initialized = True

    def _init_client(self) -> QdrantClient:
        """Initializes Qdrant client in remote server mode or local on-disk mode."""
        if settings.QDRANT_URL:
            logger.info(f"Connecting to remote Qdrant at {settings.QDRANT_URL}")
            return QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=20
            )
        else:
            logger.info(f"Initializing embedded local Qdrant at {settings.QDRANT_STORAGE_PATH}")
            return QdrantClient(path=settings.QDRANT_STORAGE_PATH)

    def _ensure_collection_and_indexes(self):
        """Creates the collection and creates indexes for timestamp and category filtering."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=qmodels.Distance.COSINE
                    )
                )

            # Create payload indexes for fast filtered searches
            self._create_payload_indexes()

        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection/indexes: {e}")

    def _create_payload_indexes(self):
        """Creates payload indexes on published_timestamp, category, publisher, and article_id."""
        index_specs = [
            ("published_timestamp", qmodels.PayloadSchemaType.FLOAT),
            ("category", qmodels.PayloadSchemaType.KEYWORD),
            ("publisher", qmodels.PayloadSchemaType.KEYWORD),
            ("article_id", qmodels.PayloadSchemaType.KEYWORD)
        ]

        for field_name, field_type in index_specs:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
            except Exception:
                pass  # Index may already exist

    def upsert_chunks(self, chunks: List[ArticleChunk], vectors: List[List[float]], batch_size: int = 64) -> int:
        """Stores article chunks and their vector embeddings with rich metadata payloads."""
        if not chunks or not vectors or len(chunks) != len(vectors):
            return 0

        points: List[qmodels.PointStruct] = []
        for chunk, vector in zip(chunks, vectors):
            point_id = str(uuid.uuid5(self.NAMESPACE_UUID, chunk.chunk_id))
            payload = {
                "chunk_id": chunk.chunk_id,
                "article_id": chunk.article_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "title": chunk.title,
                "publisher": chunk.publisher,
                "published_at": chunk.published_at,
                "published_timestamp": chunk.published_timestamp,
                "category": chunk.category,
                "article_url": chunk.article_url,
                "image_url": chunk.image_url
            }

            points.append(qmodels.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            ))

        total_upserted = 0
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                total_upserted += len(batch)
            except Exception as e:
                logger.error(f"Error upserting batch into Qdrant: {e}")

        logger.info(f"Successfully stored {total_upserted} chunks in Qdrant.")
        return total_upserted

    def search_news(
        self,
        query_vector: List[float],
        cutoff_timestamp: float,
        category: Optional[str] = None,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search with mandatory 30-day date range filter.
        Only retrieves chunks where published_timestamp >= cutoff_timestamp.
        """
        filter_conditions: List[qmodels.FieldCondition] = [
            qmodels.FieldCondition(
                key="published_timestamp",
                range=qmodels.Range(gte=cutoff_timestamp)
            )
        ]

        if category and category.lower() != "all":
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="category",
                    match=qmodels.MatchValue(value=category)
                )
            )

        query_filter = qmodels.Filter(must=filter_conditions)

        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True
            )

            hits: List[Dict[str, Any]] = []
            for hit in results:
                hits.append({
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                })
            return hits

        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []

    def delete_expired_articles(self, cutoff_timestamp: float) -> int:
        """
        Purges all points where published_timestamp < cutoff_timestamp.
        Enforces the strict rolling 30-day retention window.
        """
        logger.info(f"Running Qdrant retention cleanup for cutoff: {cutoff_timestamp}")
        expired_filter = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="published_timestamp",
                    range=qmodels.Range(lt=cutoff_timestamp)
                )
            ]
        )

        try:
            res = self.client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.FilterSelector(filter=expired_filter)
            )
            logger.info("Deleted expired points from Qdrant.")
            return 1
        except Exception as e:
            logger.error(f"Failed to delete expired points from Qdrant: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Returns collection stats such as points count and storage status."""
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "collection": self.collection_name,
                "vectors_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status.value
            }
        except Exception as e:
            return {"error": str(e), "vectors_count": 0}

