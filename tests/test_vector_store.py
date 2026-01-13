"""Test ChromaDB vector store"""

import pytest
import tempfile
from pathlib import Path
from src.retrieval.vector_store import VectorStore
from src.loaders.chunker import Chunk


class TestVectorStore:
    """Test ChromaDB vector store"""

    @pytest.fixture
    def temp_store(self):
        """Create temporary vector store"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(persist_directory=Path(tmpdir))
            yield store

    def test_add_and_retrieve_chunk(self, temp_store):
        """Add chunk and retrieve by similarity"""
        chunk = Chunk(
            text="The basic personal amount for 2024 is $15,705",
            chunk_id="ITA-118-001",
            token_count=10,
            metadata={"section": "118", "reference": "ITA s.118"},
        )
        temp_store.add_chunks([chunk])

        results = temp_store.search("basic personal amount", k=1)

        assert len(results) == 1
        assert results[0].chunk_id == "ITA-118-001"

    def test_search_returns_metadata(self, temp_store):
        """Search results should include metadata"""
        chunk = Chunk(
            text="RRSP contribution limit is 18% of earned income",
            chunk_id="ITA-146-001",
            token_count=10,
            metadata={"section": "146", "reference": "ITA s.146"},
        )
        temp_store.add_chunks([chunk])

        results = temp_store.search("RRSP contribution", k=1)

        assert results[0].metadata["section"] == "146"

    def test_search_respects_k(self, temp_store):
        """Search should return at most k results"""
        chunks = [Chunk(f"Tax rule {i}", f"chunk-{i}", 5, {}) for i in range(10)]
        temp_store.add_chunks(chunks)

        results = temp_store.search("tax rule", k=3)

        assert len(results) == 3

    def test_persistence(self):
        """Store should persist and reload"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persist_path = Path(tmpdir)

            # Create store and add chunk
            store1 = VectorStore(persist_directory=persist_path)
            chunk = Chunk("Persistent data", "persist-001", 5, {})
            store1.add_chunks([chunk])

            # Create new store pointing to same directory
            store2 = VectorStore(persist_directory=persist_path)
            results = store2.search("persistent", k=1)

            assert len(results) == 1
            assert results[0].chunk_id == "persist-001"

    def test_empty_search(self, temp_store):
        """Search on empty store returns empty list"""
        results = temp_store.search("anything", k=5)
        assert results == []

    def test_count(self, temp_store):
        """Count should return number of chunks"""
        assert temp_store.count() == 0

        chunks = [Chunk(f"Text {i}", f"id-{i}", 5, {}) for i in range(5)]
        temp_store.add_chunks(chunks)

        assert temp_store.count() == 5

    def test_search_similarity_ranking(self, temp_store):
        """More similar results should rank higher"""
        chunks = [
            Chunk("RRSP deduction rules", "rrsp-1", 5, {}),
            Chunk("TFSA withdrawal rules", "tfsa-1", 5, {}),
            Chunk("Capital gains tax", "cg-1", 5, {}),
        ]
        temp_store.add_chunks(chunks)

        results = temp_store.search("RRSP deduction", k=3)

        # First result should be most similar
        assert results[0].chunk_id == "rrsp-1"
