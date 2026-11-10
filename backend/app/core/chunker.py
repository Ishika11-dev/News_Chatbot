from typing import List
from app.schemas.news import CleanedArticle, ArticleChunk
from app.utils.date_utils import format_iso_utc

class ArticleChunker:
    """Splits cleaned news articles into overlapping chunks for embedding generation."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text(self, text: str) -> List[str]:
        """Recursive character splitting strategy using paragraphs and sentences."""
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        chunks: List[str] = []
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            if len(current_chunk) + len(p) + 2 <= self.chunk_size:
                current_chunk = f"{current_chunk}\n\n{p}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(p) > self.chunk_size:
                    sentences = p.replace(". ", ".\n").split("\n")
                    sub_chunk = ""
                    for s in sentences:
                        s = s.strip()
                        if not s:
                            continue
                        if len(sub_chunk) + len(s) + 1 <= self.chunk_size:
                            sub_chunk = f"{sub_chunk} {s}".strip()
                        else:
                            if sub_chunk:
                                chunks.append(sub_chunk)
                            sub_chunk = s
                    if sub_chunk:
                        current_chunk = sub_chunk
                else:
                    current_chunk = p

        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [text[:self.chunk_size]]

    def chunk_article(self, article: CleanedArticle) -> List[ArticleChunk]:
        """Converts an article into a list of ArticleChunk models with full metadata."""
        full_text = f"{article.title}. {article.content}"
        raw_chunks = self._split_text(full_text)
        result: List[ArticleChunk] = []

        for idx, text in enumerate(raw_chunks):
            chunk_id = f"{article.article_id}_{idx}"
            chunk = ArticleChunk(
                chunk_id=chunk_id,
                article_id=article.article_id,
                chunk_index=idx,
                text=text,
                title=article.title,
                publisher=article.publisher,
                published_at=format_iso_utc(article.published_at),
                published_timestamp=article.published_timestamp,
                category=article.category,
                article_url=article.article_url,
                image_url=article.image_url
            )
            result.append(chunk)

        return result

    def chunk_articles(self, articles: List[CleanedArticle]) -> List[ArticleChunk]:
        """Batch chunks multiple articles."""
        all_chunks: List[ArticleChunk] = []
        for article in articles:
            all_chunks.extend(self.chunk_article(article))
        return all_chunks

