"""Embedding generation for RAG retrieval"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class EmbedderConfig:
    """Configuration for embedding model"""

    model_name: str = "all-MiniLM-L6-v2"
    use_api: bool = False
    api_key: Optional[str] = None
    batch_size: int = 32


class Embedder:
    """Generate embeddings using local or API models"""

    def __init__(self, config: EmbedderConfig):
        self.config = config
        self._model = None
        self._client = None

        if config.use_api:
            self._init_api()
        else:
            self._init_local()

    def _init_local(self):
        """Initialize local sentence-transformers model"""
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.config.model_name)

    def _init_api(self):
        """Initialize OpenAI API client"""
        from openai import OpenAI

        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required but not provided")
        if self.config.model_name == "all-MiniLM-L6-v2":
            raise ValueError(
                "Embedding model 'all-MiniLM-L6-v2' is a local sentence-transformers model. "
                "Use an OpenAI embedding model (e.g., text-embedding-3-small) when --use-api is set."
            )
        self._client = OpenAI(api_key=api_key)

    def embed(self, text: str) -> list[float]:
        """Embed single text"""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        if self.config.use_api:
            return self._embed_api(text)
        return self._embed_local(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch of texts"""
        if self.config.use_api:
            return [self._embed_api(t) for t in texts]
        return self._embed_local_batch(texts)

    def _embed_local(self, text: str) -> list[float]:
        """Embed using local model"""
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def _embed_local_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed using local model"""
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            batch_size=self.config.batch_size,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def _embed_api(self, text: str) -> list[float]:
        """Embed using OpenAI API"""
        response = self._client.embeddings.create(
            model=self.config.model_name,
            input=text,
        )
        return response.data[0].embedding
