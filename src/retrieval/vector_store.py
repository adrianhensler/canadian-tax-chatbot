"""ChromaDB vector store wrapper"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import chromadb
from chromadb.config import Settings

from ..loaders.chunker import Chunk
from .embedder import Embedder, EmbedderConfig


@dataclass
class SearchResult:
    """Result from vector search"""

    chunk_id: str
    text: str
    metadata: dict
    score: float


class VectorStore:
    """ChromaDB-based vector store for ITA chunks"""

    COLLECTION_NAME = "ita_chunks"

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        embedder_config: Optional[EmbedderConfig] = None,
    ):
        self.persist_directory = persist_directory

        # Initialize ChromaDB
        if persist_directory:
            self._client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            self._client = chromadb.Client()

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "Income Tax Act chunks"},
        )

        # Initialize embedder
        config = embedder_config or EmbedderConfig()
        if config.use_api and config.model_name == "all-MiniLM-L6-v2":
            config.model_name = "text-embedding-3-small"
            print("Note: use_api enabled; defaulting embedding model to text-embedding-3-small")
        self._embedder = Embedder(config)

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Add chunks to the vector store"""
        if not chunks:
            return

        texts = [c.text for c in chunks]
        ids = [c.chunk_id for c in chunks]
        # ChromaDB requires non-empty metadata dict
        metadatas = [c.metadata if c.metadata else {"type": "unknown"} for c in chunks]

        # Generate embeddings
        embeddings = self._embedder.embed_batch(texts)

        self._collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

    def search(self, query: str, k: int = 5) -> list[SearchResult]:
        """Search for similar chunks"""
        if self._collection.count() == 0:
            return []

        query_embedding = self._embedder.embed(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        for i in range(len(results["ids"][0])):
            search_results.append(
                SearchResult(
                    chunk_id=results["ids"][0][i],
                    text=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                    score=1 - results["distances"][0][i],  # Convert distance to similarity
                )
            )

        return search_results

    def count(self) -> int:
        """Return number of chunks in store"""
        return self._collection.count()
