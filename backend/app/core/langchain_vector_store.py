import os
from pathlib import Path
from typing import List, Optional, Any, Tuple, Dict
import time
import random
import requests

# Disable Windows symlink warning for Hugging Face cache
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore

from app.config import settings
from app.utils.logger import logger

# Module-level singletons to avoid local file locking conflicts & redundant API calls
_qdrant_client: Optional[QdrantClient] = None
_vector_store: Optional[QdrantVectorStore] = None
_embeddings: Optional[Any] = None


class StorageResult(tuple):
    """
    Tuple containing (chunks_stored, tokens_used).
    Supports unpacking: `stored_count, tokens_used = add_documents_to_qdrant(...)`
    Supports named access: `result.chunks_stored`, `result.tokens_used`
    Supports integer comparison for full backward compatibility: `if result == 0:`
    """
    def __new__(cls, chunks_stored: int, tokens_used: int):
        return super().__new__(cls, (chunks_stored, tokens_used))

    @property
    def chunks_stored(self) -> int:
        return self[0]

    @property
    def tokens_used(self) -> int:
        return self[1]

    def __int__(self) -> int:
        return self[0]

    def __index__(self) -> int:
        return self[0]

    def __eq__(self, other):
        if isinstance(other, int):
            return self[0] == other
        return super().__eq__(other)

    def __lt__(self, other):
        if isinstance(other, int):
            return self[0] < other
        return super().__lt__(other)

    def __gt__(self, other):
        if isinstance(other, int):
            return self[0] > other
        return super().__gt__(other)

    def __le__(self, other):
        if isinstance(other, int):
            return self[0] <= other
        return super().__le__(other)

    def __ge__(self, other):
        if isinstance(other, int):
            return self[0] >= other
        return super().__ge__(other)


class RobustJinaEmbeddings(Embeddings):
    """
    Resilient Jina AI Embeddings client with:
    1. Real token tracking (captures 'usage.total_tokens' from API response)
    2. Retry-After header inspection on HTTP 429
    3. Transient-only retries with exponential backoff and randomized jitter
    4. Fast failure on non-transient client errors (400, 401, 403, 404)
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "jina-embeddings-v3",
        max_retries: int = 4,
        timeout: int = 30,
        endpoint: str = "https://api.jina.ai/v1/embeddings"
    ):
        self.api_key = api_key.strip() if api_key else ""
        self.model_name = (model_name or "jina-embeddings-v3").strip()
        self.max_retries = max_retries
        self.timeout = timeout
        self.endpoint = endpoint
        self.session = requests.Session()

        # Token metrics
        self.total_tokens_used: int = 0
        self.last_batch_tokens: int = 0

    def _call_api_with_retry(self, texts: List[str], task: Optional[str] = None) -> List[List[float]]:
        if not texts:
            return []

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "input": texts,
        }
        if task:
            payload["task"] = task

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                # 1. Non-transient client errors (400, 401, 403, 404) -> Fail fast immediately
                if response.status_code in (400, 401, 403, 404):
                    err_body = response.text
                    raise RuntimeError(f"Jina API non-transient error {response.status_code}: {err_body}")

                # 2. Rate limit (HTTP 429) -> Respect Retry-After header with jitter
                if response.status_code == 429:
                    retry_after_hdr = response.headers.get("Retry-After")
                    if retry_after_hdr:
                        try:
                            wait_seconds = float(retry_after_hdr) + random.uniform(0.5, 1.5)
                        except ValueError:
                            wait_seconds = (2.0 ** attempt) + random.uniform(0.5, 1.5)
                    else:
                        wait_seconds = (2.0 ** attempt) + random.uniform(0.5, 1.5)

                    if attempt < self.max_retries:
                        logger.warning(
                            f"[Jina Rate Limit 429] Waiting {wait_seconds:.2f}s before retry "
                            f"(attempt {attempt + 1}/{self.max_retries})..."
                        )
                        time.sleep(wait_seconds)
                        continue
                    else:
                        raise RuntimeError(f"Jina rate limit exceeded after {self.max_retries} retries: {response.text}")

                # 3. Transient server errors (500, 502, 503, 504) -> Exponential backoff + jitter
                if response.status_code in (500, 502, 503, 504):
                    wait_seconds = (2.0 ** attempt) + random.uniform(0.5, 1.5)
                    if attempt < self.max_retries:
                        logger.warning(
                            f"[Jina Server Error {response.status_code}] Retrying in {wait_seconds:.2f}s "
                            f"(attempt {attempt + 1}/{self.max_retries})..."
                        )
                        time.sleep(wait_seconds)
                        continue
                    else:
                        raise RuntimeError(f"Jina server error {response.status_code}: {response.text}")

                response.raise_for_status()
                data = response.json()

                if "data" not in data:
                    raise RuntimeError(f"Malformed Jina response (missing 'data'): {data}")

                # Real token tracking from Jina API usage metadata
                usage = data.get("usage", {})
                batch_tokens = usage.get("total_tokens", 0)
                self.last_batch_tokens = batch_tokens
                self.total_tokens_used += batch_tokens

                # Sort embeddings by index to preserve input order
                sorted_items = sorted(data["data"], key=lambda item: item.get("index", 0))
                return [item["embedding"] for item in sorted_items]

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = e
                wait_seconds = (2.0 ** attempt) + random.uniform(0.5, 1.5)
                if attempt < self.max_retries:
                    logger.warning(
                        f"[Jina Network Issue] {e.__class__.__name__}. Retrying in {wait_seconds:.2f}s "
                        f"(attempt {attempt + 1}/{self.max_retries})..."
                    )
                    time.sleep(wait_seconds)
                    continue
                else:
                    raise RuntimeError(f"Jina network connection failed after {self.max_retries} retries: {e}")

        raise RuntimeError(f"Jina API failed after {self.max_retries} retries: {last_error}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of document chunk texts using passage task for retrieval."""
        task = "retrieval.passage" if "v3" in self.model_name else None
        return self._call_api_with_retry(texts, task=task)

    def embed_query(self, text: str) -> List[float]:
        """Embeds a single query string using query task for retrieval."""
        task = "retrieval.query" if "v3" in self.model_name else None
        results = self._call_api_with_retry([text], task=task)
        if not results:
            return []
        return results[0]


def get_embeddings() -> RobustJinaEmbeddings:
    """Initializes embeddings (Robust Jina AI cloud API with retry & token tracking)."""
    global _embeddings
    if _embeddings is not None:
        return _embeddings

    _embeddings = RobustJinaEmbeddings(
        api_key=settings.JINA_API_KEY,
        model_name=(settings.EMBEDDING_MODEL_NAME or "jina-embeddings-v3").strip()
    )
    return _embeddings


def get_qdrant_client() -> QdrantClient:
    """Returns a singleton QdrantClient instance (local on-disk or remote)."""
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client

    qdrant_url = getattr(settings, "QDRANT_URL", None)
    if qdrant_url:
        _qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=getattr(settings, "QDRANT_API_KEY", None) or None,
            timeout=20
        )
    else:
        storage_path = Path(settings.QDRANT_STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)
        _qdrant_client = QdrantClient(path=str(storage_path))

    return _qdrant_client


def get_vector_store() -> QdrantVectorStore:
    """
    Initializes and returns LangChain's QdrantVectorStore wrapper.
    Ensures the collection exists with the correct vector dimensions.
    Uses singleton caching to avoid redundant validation calls.
    """
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    client = get_qdrant_client()
    embeddings = get_embeddings()
    collection_name = settings.QDRANT_COLLECTION_NAME

    # Check if collection exists
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)

    if exists:
        try:
            info = client.get_collection(collection_name)
            params = info.config.params.vectors
            curr_dim = getattr(params, "size", None)
            if curr_dim is None and isinstance(params, dict):
                curr_dim = getattr(list(params.values())[0], "size", None)

            if curr_dim and curr_dim != settings.EMBEDDING_DIMENSION:
                client.delete_collection(collection_name)
                exists = False
        except Exception:
            client.delete_collection(collection_name)
            exists = False

    if not exists:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=qmodels.Distance.COSINE
            )
        )

    _vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings
    )
    return _vector_store
    
def add_documents_to_qdrant(
    documents: List[Document],
    batch_size: Optional[int] = None,
    delay_seconds: Optional[float] = None
) -> StorageResult:
    """
    Embeds and stores LangChain Document chunks in Qdrant in controlled batches.
    Respects batch_size and delay_seconds to prevent API rate limit bursting (TPM/RPM).
    
    Returns:
        StorageResult: (chunks_stored, tokens_used)
    """
    if not documents:
        return StorageResult(0, 0)

    effective_batch_size = batch_size or getattr(settings, "INGESTION_BATCH_SIZE", 16)
    effective_delay = delay_seconds if delay_seconds is not None else getattr(settings, "INGESTION_BATCH_DELAY_SECONDS", 1.5)

    vector_store = get_vector_store()
    embeddings = get_embeddings()
    tokens_before = getattr(embeddings, "total_tokens_used", 0)

    total_added = 0
    errors: List[str] = []
    total_batches = (len(documents) + effective_batch_size - 1) // effective_batch_size

    print(f"[*] Embedding and storing {len(documents)} document chunks in Qdrant using {settings.EMBEDDING_MODEL_NAME} "
          f"(Batch size: {effective_batch_size}, Pacing delay: {effective_delay}s)...")

    for idx, i in enumerate(range(0, len(documents), effective_batch_size), start=1):
        batch = documents[i : i + effective_batch_size]
        batch_tokens_before = getattr(embeddings, "total_tokens_used", 0)
        t_start = time.time()
        try:
            vector_store.add_documents(batch)
            total_added += len(batch)
            batch_tokens = getattr(embeddings, "total_tokens_used", 0) - batch_tokens_before
            elapsed = time.time() - t_start
            print(f"    -> [Batch {idx}/{total_batches}] Saved {len(batch)} chunks ({total_added}/{len(documents)} total) | "
                  f"Tokens: {batch_tokens} | Elapsed: {elapsed:.2f}s")
        except Exception as e:
            err_msg = f"Batch {idx}/{total_batches} failed: {e}"
            print(f"[!] {err_msg}")
            errors.append(err_msg)

        # Apply delay between batches to respect TPM and RPM budgets (omit after last batch)
        if i + effective_batch_size < len(documents) and effective_delay > 0:
            time.sleep(effective_delay)

    total_tokens = getattr(embeddings, "total_tokens_used", 0) - tokens_before

    # If completely failed to store anything, raise so the scheduler knows
    if documents and total_added == 0:
        raise RuntimeError(f"Qdrant vector storage completely failed: {'; '.join(errors)}")

    print(f"[✓] Successfully stored {total_added}/{len(documents)} document chunks in Qdrant | Total tokens consumed: {total_tokens}")
    return StorageResult(total_added, total_tokens)

# ==============================================================================
# Standalone Manual Test Block (Runs only when executed directly)
# ==============================================================================
if __name__ == "__main__":
    import sys
    from datetime import datetime, timezone, timedelta

    # Ensure backend directory is in path
    backend_dir = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(backend_dir))

    from app.ingestion import NewsIngestionPipeline

    print("=" * 70)
    print("  PHASE 3: LANGCHAIN VECTOR STORE & EMBEDDINGS TEST")
    print("=" * 70)

    # 1. Fetch small batch of fresh news
    print("\n[1] Fetching a small batch of news articles to test storage...")
    ingestor = NewsIngestionPipeline()
    all_chunks = ingestor.load_and_chunk_news()

    # Take first 5 chunks for a fast test
    test_batch = all_chunks[:5]
    print(f"    Selected {len(test_batch)} test chunks to embed.")

    # 2. Store in Qdrant
    print("\n[2] Storing test chunks in LangChain QdrantVectorStore...")
    add_documents_to_qdrant(test_batch)

    # 3. Test Similarity Search
    print("\n[3] Testing LangChain Vector Search on Qdrant:")
    vector_store = get_vector_store()
    query = test_batch[0].metadata.get("title", "technology")
    print(f"    Search Query: '{query}'")

    results = vector_store.similarity_search(query, k=2)
    print(f"    Found {len(results)} matching documents from Qdrant:")
    for idx, doc in enumerate(results, 1):
        print(f"\n    Match [{idx}]:")
        print(f"    Title    : {doc.metadata.get('title')}")
        print(f"    Publisher: {doc.metadata.get('publisher')}")
        print(f"    URL      : {doc.metadata.get('url')}")
        print(f"    Snippet  : {doc.page_content[:150]}...")

    print("\n" + "=" * 70)
    print("  [SUCCESS] Phase 3 LangChain Vector Store verified!")
    print("=" * 70)

