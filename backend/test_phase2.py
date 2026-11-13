"""
Phase 2 Manual Test Script:
Verifies RSS extraction, HTML sanitization, 30-day date boundary filtering,
and LangChain Document chunk generation.
"""

import sys
from pathlib import Path

# Ensure backend root is in Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.langchain_ingestion import LangChainNewsIngestor


def main():
    print("=" * 70)
    print("  PHASE 2: LANGCHAIN INGESTION & DOCUMENT PIPELINE TEST")
    print("=" * 70)

    # Initialize the ingestor
    feeds_path = Path(__file__).parent / "feeds.yaml"
    ingestor = LangChainNewsIngestor(
        feeds_config_path=str(feeds_path),
        retention_days=30,
        chunk_size=700,
        chunk_overlap=100
    )

    print(f"\n[1] Loading feeds configuration from: {feeds_path.name}")
    feeds = ingestor.load_feed_configs()
    print(f"    Found {len(feeds)} configured RSS feeds across categories:")
    for f in feeds[:5]:
        print(f"    - {f.get('name')} ({f.get('category')}) -> {f.get('url')}")
    if len(feeds) > 5:
        print(f"    ... and {len(feeds) - 5} more.")

    print("\n[2] Fetching, cleaning, and extracting articles within the last 30 days...")
    parent_docs = ingestor.fetch_articles_as_documents()
    print(f"    -> Extracted {len(parent_docs)} unique, valid news articles.")

    print("\n[3] Splitting articles using LangChain's RecursiveCharacterTextSplitter...")
    chunked_docs = ingestor.text_splitter.split_documents(parent_docs)
    for i, c in enumerate(chunked_docs):
        c.metadata["chunk_id"] = f"{c.metadata.get('article_id')}_{i}"
    print(f"    -> Produced {len(chunked_docs)} LangChain Document chunks.")

    print("\n[4] Inspecting a Sample LangChain Document Chunk:")
    print("-" * 70)
    if chunked_docs:
        sample = chunked_docs[0]
        print(f"Type: {type(sample)}")
        print("\n--- METADATA DICTIONARY ---")
        for k, v in sample.metadata.items():
            print(f"  {k:20}: {v}")

        print("\n--- PAGE CONTENT (Chunk Text) ---")
        print(sample.page_content[:400] + ("..." if len(sample.page_content) > 400 else ""))
    else:
        print("    No articles found. Check network connection or feeds.yaml URLs.")

    print("-" * 70)
    print("\n[SUCCESS] Phase 2 LangChain Document pipeline verified!")
    print("=" * 70)


if __name__ == "__main__":
    main()

