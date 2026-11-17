"""
Constructs LangChain Document objects with rich metadata for vector storage.
"""

from langchain_core.documents import Document


class DocumentBuilder:
    """Builds standardized LangChain Document instances from cleaned article fields."""

    @staticmethod
    def build(
        title: str,
        body: str,
        article_id: str,
        publisher: str,
        published_at: str,
        published_timestamp: float,
        url: str,
        category: str
    ) -> Document:
        """
        Creates a LangChain Document with formatted page_content
        and standardized metadata.
        """
        page_content = f"{title}\n\n{body}"

        metadata = {
            "article_id": article_id,
            "title": title,
            "publisher": publisher,
            "published_at": published_at,
            "published_timestamp": float(published_timestamp),
            "url": url,
            "category": category
        }

        return Document(page_content=page_content, metadata=metadata)

