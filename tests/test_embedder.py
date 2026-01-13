"""Test embedding generation"""

import pytest
import os
from src.retrieval.embedder import Embedder, EmbedderConfig


class TestEmbedder:
    """Test embedding generation"""

    @pytest.fixture
    def local_embedder(self):
        """Create local embedder for testing"""
        config = EmbedderConfig(
            model_name="all-MiniLM-L6-v2",
            use_api=False,
        )
        return Embedder(config)

    def test_embed_single_text(self, local_embedder):
        """Embedder should produce vector for single text"""
        text = "What is the basic personal amount for 2024?"
        embedding = local_embedder.embed(text)

        assert len(embedding) == 384  # MiniLM dimension
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_batch(self, local_embedder):
        """Embedder should handle batch efficiently"""
        texts = [
            "RRSP contribution limit",
            "TFSA withdrawal rules",
            "Capital gains tax rate",
        ]
        embeddings = local_embedder.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)

    def test_embed_empty_text_raises(self, local_embedder):
        """Empty text should raise ValueError"""
        with pytest.raises(ValueError):
            local_embedder.embed("")

    def test_embed_long_text_doesnt_crash(self, local_embedder):
        """Text exceeding max length should be handled gracefully"""
        long_text = "tax " * 1000  # Very long
        embedding = local_embedder.embed(long_text)

        assert len(embedding) == 384  # Should still work

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY"
    )
    def test_api_embedder_integration(self):
        """Test OpenAI API embedder (requires API key)"""
        config = EmbedderConfig(
            model_name="text-embedding-3-small",
            use_api=True,
        )
        embedder = Embedder(config)

        embedding = embedder.embed("Canadian tax question")
        assert len(embedding) == 1536  # OpenAI small dimension

    def test_embeddings_are_deterministic(self, local_embedder):
        """Same text should produce same embedding"""
        text = "RRSP contribution limit"

        embedding1 = local_embedder.embed(text)
        embedding2 = local_embedder.embed(text)

        # Should be identical (within floating point precision)
        for v1, v2 in zip(embedding1, embedding2):
            assert abs(v1 - v2) < 1e-6
