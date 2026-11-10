import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Generator, Tuple
import requests

from app.config import settings
from app.core.embeddings import GeminiEmbedder
from app.core.vector_store import QdrantNewsStore
from app.schemas.chat import SourceCitation, ChatResponse
from app.utils.date_utils import get_cutoff_timestamp, format_iso_utc
from app.utils.logger import logger

class NewsRAGEngine:
    """End-to-end RAG Engine for answering news queries strictly using the 30-day vector store."""

    SYSTEM_PROMPT = """You are an AI News Intelligence Chatbot. Your goal is to answer the user's question accurately, objectively, and factually, strictly based ONLY on the verified news context provided below.

MANDATORY RULES:
1. Answer ONLY based on the facts provided in the Context below. Do NOT use prior knowledge to invent, extrapolate, or hallucinate news facts.
2. If the provided context does not contain sufficient information to answer the question, clearly state: "Based on verified news published in the last 30 days, I do not have sufficient information to answer this question."
3. Every factual statement or paragraph in your answer MUST cite its source using bracketed numbers like [1], [2], corresponding to the source entries in the Context.
4. Keep your answer well-structured, concise, and professional.
5. Today's date is: {current_date_utc}.

CONTEXT:
{context_block}
"""

    def __init__(
        self,
        embedder: Optional[GeminiEmbedder] = None,
        vector_store: Optional[QdrantNewsStore] = None
    ):
        self.embedder = embedder or GeminiEmbedder()
        self.vector_store = vector_store or QdrantNewsStore()
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self._sdk_client = None
        self._init_llm_client()

    def _init_llm_client(self):
        """Initializes google-genai SDK client if available."""
        if not self.api_key:
            logger.warning("Gemini API key is missing. LLM generation will be unavailable.")
            return

        try:
            from google import genai
            self._sdk_client = genai.Client(api_key=self.api_key)
            logger.info("Initialized Google GenAI SDK client for chat generation.")
        except Exception as e:
            logger.info(f"Google GenAI SDK not initialized ({e}). Will use HTTP streaming API.")

    def retrieve_context(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 6
    ) -> Tuple[List[Dict[str, Any]], List[SourceCitation]]:
        """
        Embeds the user query, applies 30-day cutoff, and queries Qdrant for top matching chunks.
        """
        cutoff_timestamp = get_cutoff_timestamp(retention_days=settings.RETENTION_DAYS)
        query_vector = self.embedder.embed_query(query)

        hits = self.vector_store.search_news(
            query_vector=query_vector,
            cutoff_timestamp=cutoff_timestamp,
            category=category,
            limit=top_k
        )

        sources: List[SourceCitation] = []
        seen_urls = set()

        for h in hits:
            payload = h.get("payload", {})
            url = payload.get("article_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append(
                    SourceCitation(
                        title=payload.get("title", "Untitled"),
                        publisher=payload.get("publisher", "Unknown"),
                        published_at=payload.get("published_at", ""),
                        url=url,
                        category=payload.get("category"),
                        score=round(h.get("score", 0.0), 3)
                    )
                )

        return hits, sources

    def _build_context_block(self, hits: List[Dict[str, Any]]) -> str:
        """Formats retrieved chunks into a numbered context string."""
        if not hits:
            return "No recent news articles matched your search."

        context_parts = []
        for idx, h in enumerate(hits, 1):
            p = h.get("payload", {})
            title = p.get("title", "")
            publisher = p.get("publisher", "")
            date = p.get("published_at", "")
            text = p.get("text", "")
            context_parts.append(f"[{idx}] Title: {title}\nPublisher: {publisher} | Date: {date}\nContent: {text}")

        return "\n\n".join(context_parts)

    def answer_query(
        self,
        query: str,
        category: Optional[str] = None,
        session_id: Optional[str] = None,
        top_k: int = 6
    ) -> ChatResponse:
        """Standard synchronous RAG response generator."""
        hits, sources = self.retrieve_context(query, category=category, top_k=top_k)

        # Fallback if no relevant news or very low score
        if not hits or all(h.get("score", 0.0) < settings.SIMILARITY_THRESHOLD for h in hits):
            return ChatResponse(
                answer="Based on verified news published in the last 30 days, I do not have sufficient information to answer your question.",
                sources=[],
                session_id=session_id
            )

        context_block = self._build_context_block(hits)
        prompt = self.SYSTEM_PROMPT.format(
            current_date_utc=format_iso_utc(datetime.now(timezone.utc)),
            context_block=context_block
        )

        # Call Gemini LLM
        answer_text = self._call_gemini(prompt=prompt, user_query=query)

        return ChatResponse(
            answer=answer_text,
            sources=sources,
            session_id=session_id
        )

    def _call_gemini(self, prompt: str, user_query: str) -> str:
        """Calls Gemini model with system prompt and user query."""
        if self._sdk_client:
            try:
                full_contents = f"{prompt}\n\nUser Question: {user_query}"
                response = self._sdk_client.models.generate_content(
                    model=self.model,
                    contents=full_contents
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                logger.warning(f"SDK generation failed ({e}), falling back to REST.")

        # REST API Call
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"text": f"\n\nUser Question: {user_query}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            logger.error(f"Gemini API error {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Error calling Gemini LLM: {e}")

        return "I encountered an error generating an answer based on the retrieved news."

    def stream_answer(
        self,
        query: str,
        category: Optional[str] = None,
        session_id: Optional[str] = None,
        top_k: int = 6
    ) -> Generator[str, None, None]:
        """
        Yields Server-Sent Events (SSE) data chunks for real-time streaming to the UI.
        1. Emits initial metadata event with sources.
        2. Streams text tokens from Gemini.
        3. Emits completion event.
        """
        hits, sources = self.retrieve_context(query, category=category, top_k=top_k)

        # 1. Send sources event
        sources_payload = [s.model_dump() for s in sources]
        yield f"event: sources\ndata: {json.dumps(sources_payload)}\n\n"

        if not hits or all(h.get("score", 0.0) < settings.SIMILARITY_THRESHOLD for h in hits):
            fallback_msg = "Based on verified news published in the last 30 days, I do not have sufficient information to answer your question."
            yield f"event: token\ndata: {json.dumps({'delta': fallback_msg})}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
            return

        context_block = self._build_context_block(hits)
        prompt = self.SYSTEM_PROMPT.format(
            current_date_utc=format_iso_utc(datetime.now(timezone.utc)),
            context_block=context_block
        )

        # 2. Stream generation
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"text": f"\n\nUser Question: {user_query if 'user_query' in locals() else query}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024
            }
        }

        try:
            with requests.post(url, json=payload, stream=True, timeout=30) as r:
                for line in r.iter_lines():
                    if line:
                        decoded = line.decode("utf-8")
                        if decoded.startswith("data: "):
                            data_str = decoded[6:]
                            try:
                                chunk_json = json.loads(data_str)
                                candidates = chunk_json.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    if parts:
                                        token = parts[0].get("text", "")
                                        if token:
                                            yield f"event: token\ndata: {json.dumps({'delta': token})}\n\n"
                            except Exception:
                                pass
        except Exception as e:
            logger.error(f"Error streaming from Gemini: {e}")
            yield f"event: token\ndata: {json.dumps({'delta': ' [Error generating response]'})}\n\n"

        yield "event: done\ndata: [DONE]\n\n"

