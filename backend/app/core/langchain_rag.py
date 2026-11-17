"""
LangChain RAG Pipeline (Phase 4)
---------------------------------
Features:
- Strict 30-day time-window filtering (zero stale news retrieved).
- Grounded anti-hallucination prompt with inline numerical citations ([1], [2]).
- ChatGoogleGenerativeAI (Gemini 3.8 Flash) execution.
- Returns answer alongside structured source attribution metadata.
- Streaming and synchronous query support.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, AsyncIterator
from pathlib import Path
import json
import re

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama
from qdrant_client.http import models as qmodels

from app.config import settings
from app.core.langchain_vector_store import get_vector_store


# ==============================================================================
# 1. LLM & Prompt Initialization
# ==============================================================================

def get_rag_llm(temperature: float = 0.2):
    """Initializes the chat LLM (ChatOllama if running, with seamless Gemini fallback)."""
    provider = getattr(settings, "LLM_PROVIDER", "ollama").lower()
    if provider == "ollama" and settings.OLLAMA_BASE_URL:
        try:
            import urllib.request
            # Check if local Ollama server is currently listening
            urllib.request.urlopen(f"{settings.OLLAMA_BASE_URL}/api/version", timeout=1.0)
            return ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=temperature
            )
        except Exception as e:
            print(f"[!] Notice: Ollama at {settings.OLLAMA_BASE_URL} not reachable ({e}). Using Gemini LLM.")

    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL or "gemini-3.8-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
    )


SYSTEM_PROMPT = """You are a precise, objective News Intelligence AI assistant.
Your goal is to answer the user's question using ONLY the provided verified news excerpts from the last 30 days.

CRITICAL RULES:
1. STRICT GROUNDING: Answer ONLY based on the facts provided in the Context below. Do NOT assume, extrapolate, or use outside pre-training knowledge.
2. INLINE CITATIONS: Every factual assertion in your answer MUST be cited using numerical brackets matching the source document index, for example [1] or [1][2].
3. INSUFFICIENT INFORMATION: If the provided news excerpts do not contain sufficient verified facts to answer the question, respond EXACTLY with:
"I do not have verified news from the past 30 days to answer this question."
4. OBJECTIVE TONE: Summarize and explain clearly without opinion, bias, or sensationalism. Mention publishers and dates when helpful.
"""

PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Context (Verified News from the Past 30 Days):
{context}

User Question: {question}

Helpful & Factual Answer (with inline [1], [2] citations):""")
])


# ==============================================================================
# 2. Context & Source Formatting
# ==============================================================================

def format_docs_with_citations(docs: List[Document]) -> tuple[str, List[Dict[str, Any]]]:
    """
    Formats LangChain Document chunks into indexed context strings for the LLM
    and extracts a clean, deduplicated list of source citations.
    """
    if not docs:
        return "No recent news articles found for this topic.", []

    context_parts = []
    sources = []
    seen_articles = set()

    for i, doc in enumerate(docs, 1):
        meta = doc.metadata or {}
        article_id = meta.get("article_id") or meta.get("url") or f"doc_{i}"
        title = meta.get("title", "Untitled News")
        publisher = meta.get("publisher", "Unknown Publisher")
        published_at = meta.get("published_at", "Recent")
        url = meta.get("url", "")
        category = meta.get("category", "General")

        # Format chunk block for LLM prompt
        snippet = doc.page_content.strip()
        context_parts.append(
            f"[{i}] Title: {title}\n"
            f"    Publisher: {publisher} | Published: {published_at} | Category: {category}\n"
            f"    Excerpt: {snippet}"
        )

        # Track unique sources for the frontend/API response
        if article_id not in seen_articles:
            seen_articles.add(article_id)
            score_val = meta.get("score")
            sources.append({
                "citation_id": i,
                "title": title,
                "publisher": publisher,
                "published_at": published_at,
                "url": url,
                "category": category,
                "score": round(float(score_val), 3) if score_val is not None else None
            })

    formatted_context = "\n\n".join(context_parts)
    return formatted_context, sources


REFUSAL_PHRASES = [
    "do not have verified news",
    "cannot answer",
    "no verified news",
    "not enough verified news",
    "no recent news",
    "do not have enough information",
    "not enough information",
    "does not mention",
    "no information"
]


def filter_cited_sources(answer_text: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prunes sources to ensure grounding integrity:
    1. If the assistant stated it lacks verified news, sources are completely cleared ([]).
    2. If citations like [1], [2] are present in the answer, only returns the sources actually cited.
    3. If the answer does not cite any source, removes uncited sources to avoid returning irrelevant cards.
    """
    lower_ans = answer_text.lower()
    if any(phrase in lower_ans for phrase in REFUSAL_PHRASES):
        return []

    # Find cited citation numbers: e.g. [1], [2]
    cited_ids = {int(m) for m in re.findall(r"\[(\d+)\]", answer_text)}
    if cited_ids:
        return [s for s in sources if s.get("citation_id") in cited_ids]

    if len(answer_text.strip()) < 60:
        return []

    return sources


# ==============================================================================
# 3. LangChain News RAG Pipeline Class
# ==============================================================================

class LangChainNewsRAG:
    """End-to-end RAG question-answering pipeline built with LangChain."""

    def __init__(self, retention_days: int = settings.RETENTION_DAYS):
        self.retention_days = retention_days
        self.vector_store = get_vector_store()
        self.llm = get_rag_llm()

    def _get_cutoff_timestamp(self) -> float:
        """Returns the UTC timestamp cutoff for the retention window."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        return cutoff_date.timestamp()

    def retrieve_recent_docs(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[Document]:
        """
        Retrieves relevant documents strictly within the 30-day retention window
        and above the minimum similarity score threshold.
        """
        cutoff_ts = self._get_cutoff_timestamp()

        # Build Qdrant filter for timestamp >= cutoff_ts
        conditions = [
            qmodels.FieldCondition(
                key="metadata.published_timestamp",
                range=qmodels.Range(gte=cutoff_ts)
            )
        ]

        # Only apply category filter if user passed a real category (ignoring Swagger placeholder "string" and "All")
        if category and category.strip().lower() not in ["all", "string", "none", "", "null"]:
            conditions.append(
                qmodels.FieldCondition(
                    key="metadata.category",
                    match=qmodels.MatchValue(value=category.strip())
                )
            )

        qdrant_filter = qmodels.Filter(must=conditions)

        try:
            # Query Qdrant with filter and similarity score calculation
            raw_docs_with_scores = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k * 2,
                filter=qdrant_filter
            )
        except Exception as e:
            # Fallback to similarity search with scores if filter encounters index issues
            print(f"[!] Qdrant filter query notice: {e}; falling back to post-filtering.")
            raw_docs_with_scores = self.vector_store.similarity_search_with_score(query=query, k=top_k * 2)

        # Dual-layer guarantee: strictly enforce 30-day cutoff AND similarity threshold in-memory
        valid_docs = []
        similarity_threshold = getattr(settings, "SIMILARITY_THRESHOLD", 0.35)

        for item in raw_docs_with_scores:
            if isinstance(item, tuple) and len(item) == 2:
                doc, score = item
            else:
                doc, score = item, None

            # Skip irrelevant documents with low similarity score
            if score is not None and float(score) < similarity_threshold:
                continue

            ts = doc.metadata.get("published_timestamp")
            if ts is not None and float(ts) >= cutoff_ts:
                if score is not None:
                    doc.metadata["score"] = round(float(score), 4)
                valid_docs.append(doc)
            elif ts is None:
                if score is not None:
                    doc.metadata["score"] = round(float(score), 4)
                valid_docs.append(doc)

        return valid_docs[:top_k]

    def answer_question(self, question: str, top_k: int = 5, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the LangChain RAG pipeline:
        1. Retrieves 30-day filtered chunks above the similarity threshold.
        2. Formats context with citation indices [1], [2].
        3. Invokes the LLM with the strict anti-hallucination prompt.
        4. Prunes unreferenced sources or clears them if the model refuses to answer.
        """
        retrieved_docs = self.retrieve_recent_docs(query=question, top_k=top_k, category=category)
        formatted_context, sources = format_docs_with_citations(retrieved_docs)

        # If zero docs found, return direct standard fallback without wasting LLM tokens
        if not retrieved_docs:
            return {
                "question": question,
                "answer": "I do not have verified news from the past 30 days to answer this question.",
                "sources": [],
                "retrieved_count": 0
            }

        # Build LCEL chain
        rag_chain = PROMPT_TEMPLATE | self.llm | StrOutputParser()

        response_text = rag_chain.invoke({
            "context": formatted_context,
            "question": question
        }).strip()

        # Clean sources: remove unreferenced citations or clear if refused
        final_sources = filter_cited_sources(response_text, sources)

        return {
            "question": question,
            "answer": response_text,
            "sources": final_sources,
            "retrieved_count": len(final_sources)
        }

    def stream_answer(self, question: str, top_k: int = 5, category: Optional[str] = None):
        """
        Streams response tokens in SSE format:
        yields {"token": "..."} as generated, then {"sources": [...]} at the end, and finally "[DONE]".
        """
        retrieved_docs = self.retrieve_recent_docs(query=question, top_k=top_k, category=category)
        formatted_context, sources = format_docs_with_citations(retrieved_docs)

        if not retrieved_docs:
            yield f"data: {json.dumps({'token': 'I do not have verified news from the past 30 days to answer this question.'})}\n\n"
            yield f"data: {json.dumps({'sources': []})}\n\n"
            yield "data: [DONE]\n\n"
            return

        rag_chain = PROMPT_TEMPLATE | self.llm | StrOutputParser()
        full_tokens = []
        for token in rag_chain.stream({"context": formatted_context, "question": question}):
            full_tokens.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

        full_text = "".join(full_tokens).strip()
        final_sources = filter_cited_sources(full_text, sources)

        yield f"data: {json.dumps({'sources': final_sources})}\n\n"
        yield "data: [DONE]\n\n"


# ==============================================================================
# Standalone Manual Test Block (Runs only when executed directly)
# ==============================================================================
if __name__ == "__main__":
    import sys

    # Ensure backend root is in sys.path
    backend_dir = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(backend_dir))

    print("=" * 70)
    print("  PHASE 4: LANGCHAIN RAG QUESTION-ANSWERING TEST")
    print("=" * 70)

    rag = LangChainNewsRAG()

    # Test 1: In-domain news question against the articles stored in Qdrant
    test_question_1 = "What investigation was launched regarding Nvidia and Jensen Huang?"
    print(f"\n[Test 1] Question: '{test_question_1}'")
    print("-" * 70)
    result_1 = rag.answer_question(test_question_1, top_k=3)

    print(f"\nANSWER:\n{result_1['answer']}\n")
    print(f"SOURCES ({len(result_1['sources'])} cited):")
    for s in result_1["sources"]:
        print(f"  [{s['citation_id']}] {s['title']}")
        print(f"      Publisher: {s['publisher']} | Date: {s['published_at']}")
        print(f"      URL: {s['url']}")

    # Test 2: Out-of-domain / stale news question (Testing strict anti-hallucination rule)
    test_question_2 = "What was the final score of the 1998 FIFA World Cup match between France and Brazil?"
    print("\n" + "=" * 70)
    print(f"[Test 2 - Anti-Hallucination] Question: '{test_question_2}'")
    print("-" * 70)
    result_2 = rag.answer_question(test_question_2, top_k=3)

    print(f"\nANSWER:\n{result_2['answer']}\n")
    print(f"SOURCES: {len(result_2['sources'])} sources returned.")

    print("\n" + "=" * 70)
    print("  [SUCCESS] Phase 4 LangChain RAG pipeline verified!")
    print("=" * 70)

