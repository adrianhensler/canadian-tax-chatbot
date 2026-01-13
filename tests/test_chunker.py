"""Test section-aware chunker"""

import pytest
from pathlib import Path
from src.loaders.chunker import chunk_section, Chunk
from src.loaders.xml_parser import parse_justice_xml

FIXTURES = Path(__file__).parent / "fixtures"


class TestChunker:
    """Test section-aware chunking"""

    def test_small_section_single_chunk(self):
        """Section < max_tokens should produce single chunk"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)

        # Use a large max to ensure single chunk
        chunks = chunk_section(sections[0], max_tokens=10000)

        assert len(chunks) == 1

    def test_chunk_preserves_section_metadata(self):
        """Chunk metadata should include section number and reference"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)
        chunks = chunk_section(sections[0], max_tokens=10000)

        chunk = chunks[0]
        assert chunk.metadata["section"] == "118"
        assert chunk.metadata["reference"] == "ITA s.118"
        assert chunk.metadata["title"] == "Personal credits"

    def test_large_section_splits_at_subsection_boundary(self):
        """Large sections should split at subsection boundaries"""
        xml_path = FIXTURES / "ita_section_146.xml"
        sections = parse_justice_xml(xml_path)

        # Force splitting with small max_tokens
        chunks = chunk_section(sections[0], max_tokens=300)

        assert len(chunks) > 1
        # Each chunk should have subsection or section info
        for chunk in chunks:
            assert "subsection" in chunk.metadata or "section" in chunk.metadata

    def test_chunk_reference_format(self):
        """Subsection chunks should have proper ITA reference format"""
        xml_path = FIXTURES / "ita_section_146.xml"
        sections = parse_justice_xml(xml_path)
        chunks = chunk_section(sections[0], max_tokens=300)

        # Find a subsection chunk
        ss_chunks = [c for c in chunks if "subsection" in c.metadata]
        if ss_chunks:
            ref = ss_chunks[0].metadata["reference"]
            assert ref.startswith("ITA s.146(")

    def test_chunk_id_unique(self):
        """Each chunk should have unique ID"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)
        chunks = chunk_section(sections[0], max_tokens=500)

        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "Chunk IDs must be unique"

    def test_chunk_has_text(self):
        """All chunks should have non-empty text"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)
        chunks = chunk_section(sections[0], max_tokens=1000)

        for chunk in chunks:
            assert len(chunk.text) > 0
            assert chunk.token_count > 0

    def test_chunk_token_count_reasonable(self):
        """Token count should be reasonable (not zero, not absurdly high)"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)
        max_tokens = 1500
        chunks = chunk_section(sections[0], max_tokens=max_tokens)

        for chunk in chunks:
            # Token count should be positive and not exceed max by much
            assert chunk.token_count > 0
            assert chunk.token_count <= max_tokens * 1.1  # Allow 10% overage

    def test_section_248_large_section(self):
        """Section 248 (definitions) is very large - should chunk properly"""
        xml_path = FIXTURES / "ita_section_248.xml"
        sections = parse_justice_xml(xml_path)

        chunks = chunk_section(sections[0], max_tokens=1500)

        # Should create multiple chunks
        assert len(chunks) > 1

        # All chunks should have section 248
        for chunk in chunks:
            assert chunk.metadata["section"] == "248"

    def test_metadata_includes_source_type(self):
        """Metadata should identify this as federal statute"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)
        chunks = chunk_section(sections[0])

        for chunk in chunks:
            assert chunk.metadata["source"] == "Income Tax Act"
            assert chunk.metadata["source_abbreviation"] == "ITA"
            assert chunk.metadata["document_type"] == "federal_statute"
