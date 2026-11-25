"""
End-to-end integration and verification script for News Intelligence Ingestion Architecture:
- Direct imports from app.ingestion
- Date gate validation (Requirement 7: invalid/missing dates rejected)
- Scheduler and Admin route integration
- Local Qdrant vector storage compatibility
- RAG retrieval and citation formatting
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from langchain_core.documents import Document
from app.ingestion import (
    NewsIngestionPipeline,
    ArticleChunker,
    DocumentBuilder,
    ArticleDeduplicator,
    parse_date_to_utc,
    is_within_retention_window
)
from app.core.scheduler import scheduler_manager
from app.api.routes_admin import trigger_manual_ingestion, list_configured_feeds
from app.core.langchain_vector_store import (
    get_vector_store,
    add_documents_to_qdrant
)
from app.core.langchain_rag import LangChainNewsRAG, format_docs_with_citations, filter_cited_sources


def test_date_gate_enforcement():
    print("\n--- 1. Testing Date Gate Enforcement (Requirement 7) ---")
    now_utc = datetime.now(timezone.utc)

    # 1. Valid recent date
    iso_v, epoch_v = parse_date_to_utc((now_utc - timedelta(days=2)).isoformat())
    assert is_within_retention_window(epoch_v, retention_days=30), "Valid recent date should pass"

    # 2. Expired date (> 30 days)
    iso_old, epoch_old = parse_date_to_utc((now_utc - timedelta(days=45)).isoformat())
    assert not is_within_retention_window(epoch_old, retention_days=30), "Date older than 30 days must be rejected"

    # 3. Missing date (None)
    iso_none, epoch_none = parse_date_to_utc(None)
    assert iso_none is None and epoch_none is None, "Missing date must yield (None, None)"
    assert not is_within_retention_window(epoch_none, retention_days=30), "None date must be rejected"

    # 4. Invalid date string
    iso_inv, epoch_inv = parse_date_to_utc("invalid-date-string")
    assert iso_inv is None and epoch_inv is None, "Invalid date must yield (None, None)"
    assert not is_within_retention_window(epoch_inv, retention_days=30), "Invalid date must be rejected"

    print("[PASS] Requirement 7 verified: missing/invalid dates are never treated as current news.")


def test_pipeline_and_chunking():
    print("\n--- 2. Testing Modular Pipeline and Chunker ---")
    pipeline = NewsIngestionPipeline(retention_days=30, chunk_size=700, chunk_overlap=100)
    feeds = pipeline.load_feed_configs()
    print(f"Loaded {len(feeds)} configured feeds via FeedFetcher.")
    assert len(feeds) > 0

    builder = DocumentBuilder()
    doc = builder.build(
        title="AI Semiconductor Milestone",
        body="Next generation processors feature high memory bandwidth and low latency architectures. " * 8,
        article_id="test_semi_art_001",
        publisher="TechDaily",
        published_at=datetime.now(timezone.utc).isoformat(),
        published_timestamp=datetime.now(timezone.utc).timestamp(),
        url="https://example.com/ai-semiconductor?utm_source=test",
        category="Technology"
    )

    chunker = ArticleChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.split_documents([doc])
    print(f"Split document into {len(chunks)} chunks with chunk_id metadata.")
    assert len(chunks) > 1
    assert chunks[0].metadata["chunk_id"] == "test_semi_art_001_0"
    print("[PASS] Modular pipeline and chunking verified.")


def test_scheduler_and_admin_ingestion():
    print("\n--- 3. Testing Scheduler and Admin Trigger ---")
    assert isinstance(scheduler_manager.ingestor, NewsIngestionPipeline), "Scheduler must use NewsIngestionPipeline"

    # Check configured feeds admin route
    feed_response = list_configured_feeds()
    assert feed_response["total_feeds"] > 0
    print(f"Admin /feeds reported {feed_response['total_feeds']} feeds.")

    # Call admin trigger directly
    admin_result = trigger_manual_ingestion()
    assert admin_result["status"] == "COMPLETED"
    print(f"Admin manual ingestion completed successfully. Message: '{admin_result['message']}'")
    print("[PASS] Scheduler and admin integration verified.")


def test_qdrant_storage_and_rag():
    print("\n--- 4. Testing Local Qdrant Storage & RAG Retrieval ---")
    now_utc = datetime.now(timezone.utc)
    test_doc = Document(
        page_content="Nvidia Corporation is facing an inquiry by government officials regarding specialized AI chip exports and international trade compliance.",
        metadata={
            "article_id": "nvidia_inquiry_test_01",
            "chunk_id": "nvidia_inquiry_test_01_0",
            "title": "Government Officials Launch Nvidia AI Chip Export Inquiry",
            "publisher": "TechPolicy Review",
            "published_at": now_utc.isoformat(),
            "published_timestamp": now_utc.timestamp(),
            "url": "https://techpolicy.example.com/nvidia-inquiry",
            "category": "Technology"
        }
    )

    stored_count, _ = add_documents_to_qdrant([test_doc])
    print(f"Stored {stored_count} chunk in local Qdrant collection.")

    # Verify vector search
    vector_store = get_vector_store()
    results = vector_store.similarity_search("What inquiry was launched regarding Nvidia?", k=1)
    assert len(results) > 0
    print(f"Retrieved match from Qdrant: '{results[0].metadata.get('title')}'")
    assert "Nvidia" in results[0].page_content

    # Verify RAG retrieval filtering
    rag = LangChainNewsRAG()
    retrieved_docs = rag.retrieve_recent_docs("What inquiry was launched regarding Nvidia?", top_k=2)
    assert len(retrieved_docs) > 0
    print(f"RAG retrieved {len(retrieved_docs)} verified recent documents.")

    context_str, sources = format_docs_with_citations(retrieved_docs)
    assert len(sources) > 0
    assert "[1]" in context_str
    print(f"Citation formatting verified with {len(sources)} source(s).")

    # Verify LLM generation if available
    try:
        response = rag.answer_question("What inquiry was launched regarding Nvidia?")
        print(f"RAG Answer: {response.get('answer', '')[:120]}...")
        print(f"Citations count: {len(response.get('sources', []))}")
    except Exception as e:
        print(f"(Note: LLM inference skipped or timed out: {e})")

    print("[PASS] Local Qdrant storage and RAG retrieval verified.")


if __name__ == "__main__":
    print("=" * 70)
    print("  INGESTION REFACTORING VERIFICATION SUITE")
    print("=" * 70)
    test_date_gate_enforcement()
    test_pipeline_and_chunking()
    test_scheduler_and_admin_ingestion()
    test_qdrant_storage_and_rag()
    print("\n" + "=" * 70)
    print("  ALL INGESTION ARCHITECTURE VERIFICATIONS SUCCEEDED!")
    print("=" * 70)
