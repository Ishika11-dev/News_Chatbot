"""
Splits LangChain Document objects into vector-ready chunks with persistent metadata.
"""

from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ArticleChunker:
    """Chunks documents using RecursiveCharacterTextSplitter while attaching chunk_id."""

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Splits a list of parent Documents into chunks.
        Adds chunk_id ('{article_id}_{index}') to each chunk's metadata.
        """
        if not documents:
            return []

        chunked_docs = self.text_splitter.split_documents(documents)

        for i, chunk in enumerate(chunked_docs):
            article_id = chunk.metadata.get("article_id", "doc")
            chunk.metadata["chunk_id"] = f"{article_id}_{i}"

        return chunked_docs

