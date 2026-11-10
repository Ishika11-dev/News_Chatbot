import time
from typing import List, Optional
import requests
from app.config import settings
from app.utils.logger import logger

class GeminiEmbedder:
    """Generates vector embeddings using Google Gemini's text-embedding-004 model."""

    API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_EMBEDDING_MODEL
        self._sdk_client = None
        self._init_client()

    def _init_client(self):
        """Attempts to initialize the official google-genai SDK if available."""
        if not self.api_key:
            logger.warning("Gemini API key is not configured. Embeddings will fail until provided.")
            return

        try:
            from google import genai
            self._sdk_client = genai.Client(api_key=self.api_key)
            logger.info("Initialized Google GenAI SDK client for embeddings.")
        except Exception as e:
            logger.info(f"Google GenAI SDK not loaded ({e}). Will use HTTP REST API for embeddings.")

    def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """Generates embedding for a single string."""
        if not text or not text.strip():
            return [0.0] * settings.EMBEDDING_DIMENSION

        # 1. Try SDK if available
        if self._sdk_client:
            try:
                from google.genai import types
                response = self._sdk_client.models.embed_content(
                    model=self.model,
                    contents=text,
                    config=types.EmbedContentConfig(task_type=task_type)
                )
                if response and response.embedding and response.embedding.values:
                    return list(response.embedding.values)
            except Exception as e:
                logger.warning(f"SDK embedding failed, falling back to REST: {e}")

        # 2. REST API Fallback
        return self._embed_via_rest(text, task_type=task_type)

    def _embed_via_rest(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """Direct REST call to Gemini embedContent endpoint."""
        url = f"{self.API_BASE}/{self.model}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{self.model}",
            "content": {"parts": [{"text": text}]},
            "taskType": task_type
        }

        for attempt in range(3):
            try:
                resp = requests.post(url, json=payload, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("embedding", {}).get("values", [0.0] * settings.EMBEDDING_DIMENSION)
                elif resp.status_code == 429:
                    wait_time = (2 ** attempt) * 2
                    logger.warning(f"Rate limited (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Embedding API error {resp.status_code}: {resp.text}")
                    break
            except Exception as e:
                logger.error(f"HTTP request error during embedding: {e}")
                time.sleep(1)

        return [0.0] * settings.EMBEDDING_DIMENSION

    def embed_batch(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT", batch_size: int = 16) -> List[List[float]]:
        """Batch embeds a list of strings with rate-limiting protection."""
        embeddings: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            for text in batch:
                vec = self.embed_text(text, task_type=task_type)
                embeddings.append(vec)
            # Brief throttle to prevent RPM spikes
            if len(texts) > batch_size:
                time.sleep(0.2)
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Convenience method to embed a user search query."""
        return self.embed_text(query, task_type="RETRIEVAL_QUERY")

