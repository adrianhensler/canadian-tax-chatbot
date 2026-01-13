"""Retriever interface for the chatbot"""

from pathlib import Path
from typing import Optional
from .vector_store import VectorStore, SearchResult
from .embedder import EmbedderConfig


class Retriever:
    """High-level retrieval interface"""

    def __init__(
        self,
        corpus_path: Optional[Path] = None,
        embedder_config: Optional[EmbedderConfig] = None,
    ):
        """
        Initialize retriever with corpus.

        Args:
            corpus_path: Path to corpus directory (should contain chroma/ subdirectory)
            embedder_config: Configuration for embedding model
        """
        if corpus_path is None:
            corpus_path = Path("data/corpus/current")

        chroma_path = corpus_path / "chroma"
        if not chroma_path.exists():
            raise ValueError(f"Corpus not found at {chroma_path}")

        self._store = VectorStore(
            persist_directory=chroma_path,
            embedder_config=embedder_config,
        )

    def retrieve(self, query: str, k: int = 5) -> list[SearchResult]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Natural language question
            k: Number of results to return

        Returns:
            List of SearchResult objects ranked by relevance
        """
        return self._store.search(query, k=k)
