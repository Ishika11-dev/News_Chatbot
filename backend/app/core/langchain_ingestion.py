import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import yaml
import requests
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Tracking query parameters to strip for deduplication
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "source", "feed"
}

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 NewsIntelligence/1.0",
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8"
}


def clean_html(raw_html: Optional[str]) -> str:
    """Strips HTML tags and normalizes whitespace."""
    if not raw_html or not raw_html.strip():
        return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "noscript", "iframe", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", raw_html)

    # Normalize whitespace
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date_to_utc(date_str: Optional[str]) -> tuple[str, float]:
    """
    Parses RSS pubDate string into ISO 8601 string and epoch seconds (UTC).
    Falls back to current UTC time if date_str is missing or unparseable.
    """
    now_utc = datetime.now(timezone.utc)
    if not date_str:
        return now_utc.isoformat(), now_utc.timestamp()

    try:
        dt = date_parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat(), dt.timestamp()
    except Exception:
        return now_utc.isoformat(), now_utc.timestamp()


def canonicalize_url(url: str) -> str:
    """Strips tracking query parameters and standardizes URL for deduplication."""
    if not url:
        return ""
    url = url.strip()
    parsed = urlparse(url)
    clean_queries = [
        (k, v) for k, v in parse_qsl(parsed.query)
        if k.lower() not in TRACKING_PARAMS
    ]
    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        parsed.params,
        urlencode(clean_queries, doseq=True),
        ""
    ))


def generate_article_id(canonical_url: str) -> str:
    """Generates a stable SHA-256 identifier from canonical URL."""
    return hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()


class LangChainNewsIngestor:
    """
    Fetches RSS feeds, cleans text, deduplicates articles, and converts them
    into chunked LangChain Document objects ready for vector storage.
    """

    def __init__(
        self,
        feeds_config_path: str = "feeds.yaml",
        retention_days: int = 30,
        chunk_size: int = 700,
        chunk_overlap: int = 100
    ):
        self.feeds_config_path = Path(feeds_config_path)
        self.retention_days = retention_days
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def load_feed_configs(self) -> List[Dict[str, Any]]:
        """Loads feed list from YAML file."""
        if not self.feeds_config_path.exists():
            # Try looking one directory up (if running from backend/)
            alt_path = Path(__file__).resolve().parent.parent.parent / self.feeds_config_path.name
            if alt_path.exists():
                self.feeds_config_path = alt_path

        with open(self.feeds_config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("feeds", [])

    def fetch_articles_as_documents(self, seen_ids: Optional[Set[str]] = None) -> List[Document]:
        """
        Fetches all configured feeds, extracts fresh articles, and wraps each
        into a LangChain Document.
        """
        seen_ids = seen_ids if seen_ids is not None else set()
        feeds = self.load_feed_configs()
        documents: List[Document] = []
        cutoff_epoch = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).timestamp()

        for feed in feeds:
            feed_name = feed.get("name", "Unknown")
            feed_url = feed.get("url")
            publisher = feed.get("publisher", feed_name)
            category = feed.get("category", "General")

            try:
                resp = requests.get(feed_url, headers=REQUEST_HEADERS, timeout=12)
                resp.raise_for_status()
                parsed = feedparser.parse(resp.content)
            except Exception as e:
                print(f"[!] Warning: Failed to fetch feed '{feed_name}': {e}")
                continue

            for entry in parsed.entries:
                link = entry.get("link", "").strip()
                if not link:
                    continue

                clean_url = canonicalize_url(link)
                article_id = generate_article_id(clean_url)

                # Deduplication check
                if article_id in seen_ids:
                    continue

                # Date parsing & 30-day window check
                raw_date = entry.get("published") or entry.get("pubDate") or entry.get("updated")
                iso_date, epoch_ts = parse_date_to_utc(raw_date)

                if epoch_ts < cutoff_epoch:
                    continue  # Skip news older than 30 days

                # Content extraction & cleaning
                raw_title = entry.get("title", "")
                raw_summary = entry.get("summary", "") or entry.get("description", "")
                raw_content = ""
                content_list = entry.get("content", [])
                if content_list and isinstance(content_list, list):
                    raw_content = content_list[0].get("value", "")

                clean_title = clean_html(raw_title)
                clean_body = clean_html(raw_content or raw_summary)

                if len(clean_title) < 5 or len(clean_body) < 30:
                    continue

                seen_ids.add(article_id)

                # Compose readable page_content for LangChain
                page_content = f"{clean_title}\n\n{clean_body}"

                # Create LangChain Document with rich metadata
                doc = Document(
                    page_content=page_content,
                    metadata={
                        "article_id": article_id,
                        "title": clean_title,
                        "publisher": publisher,
                        "published_at": iso_date,
                        "published_timestamp": float(epoch_ts),
                        "url": clean_url,
                        "category": category
                    }
                )
                documents.append(doc)

        return documents

    def load_and_chunk_news(self, seen_ids: Optional[Set[str]] = None) -> List[Document]:
        """
        End-to-end ingestion pipeline:
        Fetches fresh news -> Wraps as LangChain Documents -> Chunks with RecursiveCharacterTextSplitter.
        """
        parent_docs = self.fetch_articles_as_documents(seen_ids=seen_ids)
        if not parent_docs:
            return []

        # Chunk the documents while preserving all metadata
        chunked_docs = self.text_splitter.split_documents(parent_docs)

        # Add chunk-specific index to metadata
        for i, chunk in enumerate(chunked_docs):
            chunk.metadata["chunk_id"] = f"{chunk.metadata.get('article_id')}_{i}"

        return chunked_docs

