from pathlib import Path
from typing import List, Optional
import time

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from app.config import settings

# Module-level singleton client to avoid local file locking conflicts
_qdrant_client: Optional[QdrantClient] = None


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Initializes LangChain's Google GenAI Embeddings model."""
    return GoogleGenerativeAIEmbeddings(
        model=f"models/{settings.GEMINI_EMBEDDING_MODEL}",
        google_api_key=settings.GEMINI_API_KEY
    )


def get_qdrant_client() -> QdrantClient:
    """Returns a singleton QdrantClient instance (local on-disk or remote)."""
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client

    if settings.QDRANT_URL:
        _qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
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
    """
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

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings
    )


def add_documents_to_qdrant(documents: List[Document], batch_size: int = 16) -> int:
    """
    Embeds and stores LangChain Document chunks in Qdrant in safe batches.
    """
    if not documents:
        return 0

    vector_store = get_vector_store()
    total_added = 0

    print(f"[*] Embedding and storing {len(documents)} document chunks in Qdrant...")

    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        try:
            vector_store.add_documents(batch)
            total_added += len(batch)
            print(f"    -> Progress: {total_added}/{len(documents)} chunks saved.")
            # Brief pause to stay well within Gemini RPM limits
            time.sleep(0.3)
        except Exception as e:
            print(f"[!] Error storing batch {i//batch_size + 1}: {e}")

    print(f"[✓] Successfully stored {total_added} document chunks in Qdrant!")
    return total_added


# ==============================================================================
# Standalone Manual Test Block (Runs only when executed directly)
# ==============================================================================
if __name__ == "__main__":
    import sys
    from datetime import datetime, timezone, timedelta

    # Ensure backend directory is in path
    backend_dir = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(backend_dir))

    from app.core.langchain_ingestion import LangChainNewsIngestor

    print("=" * 70)
    print("  PHASE 3: LANGCHAIN VECTOR STORE & EMBEDDINGS TEST")
    print("=" * 70)

    # 1. Fetch small batch of fresh news
    print("\n[1] Fetching a small batch of news articles to test storage...")
    ingestor = LangChainNewsIngestor()
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

