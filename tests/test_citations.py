"""Tests for citation extraction and validation."""

import pytest
from src.chat.citations import (
    Citation,
    extract_citations,
    validate_citations,
    generate_url,
)
from src.retrieval.vector_store import SearchResult


def test_citation_dataclass():
    """Test Citation dataclass structure."""
    citation = Citation(
        reference="ITA s.118(1)",
        text="The basic personal amount...",
        url="https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-118.html",
        validated=True,
    )

    assert citation.reference == "ITA s.118(1)"
    assert citation.text == "The basic personal amount..."
    assert citation.validated is True


def test_extract_citations_well_formatted():
    """Test extracting citations from well-formatted response."""
    response = """The basic personal amount for 2024 is $15,705. This is available to all Canadian residents.

Citations:
- ITA s.118(1): "There may be deducted... the basic personal amount"
- ITA s.118(2): "Additional amount for eligible dependants"
"""

    citations = extract_citations(response)

    assert len(citations) >= 2
    references = [c.reference for c in citations]
    assert "ITA s.118(1)" in references
    assert "ITA s.118(2)" in references


def test_extract_citations_with_subsections():
    """Test extracting citations with subsections and paragraphs."""
    response = """RRSP contributions are governed by specific rules.

Citations:
- ITA s.146(1): "Definition of RRSP"
- ITA s.146(5)(a): "Contribution limits"
"""

    citations = extract_citations(response)

    assert len(citations) >= 2
    references = [c.reference for c in citations]
    assert any("146(1)" in r for r in references)
    assert any("146(5)(a)" in r for r in references)


def test_extract_citations_inline():
    """Test extracting inline citations from response."""
    response = """According to ITA s.118(1), the basic personal amount is a non-refundable credit.
Section 146(1) defines RRSP contributions."""

    citations = extract_citations(response)

    # Should find at least the two inline references
    assert len(citations) >= 2
    references = [c.reference for c in citations]
    assert any("118" in r for r in references)
    assert any("146" in r for r in references)


def test_extract_citations_no_citations():
    """Test extraction when response has no citations."""
    response = "I don't have information about that in the provided context."

    citations = extract_citations(response)

    assert isinstance(citations, list)
    assert len(citations) == 0


def test_extract_citations_malformed():
    """Test graceful handling of malformed citation section."""
    response = """Some answer text.

Citations:
This is not properly formatted
- Missing colon ITA s.118(1)
"""

    # Should not crash, may extract what it can
    citations = extract_citations(response)
    assert isinstance(citations, list)


def test_validate_citations_matching():
    """Test validating citations that match retrieved chunks."""
    citations = [
        Citation(
            reference="ITA s.118(1)",
            text="Basic personal amount",
            url=None,
            validated=False,
        ),
    ]

    retrieved = [
        SearchResult(
            chunk_id="ITA-118-001",
            text="Text about basic personal amount",
            metadata={"section": "118", "reference": "ITA s.118(1)"},
            score=0.95,
        ),
    ]

    validated = validate_citations(citations, retrieved)

    assert len(validated) == 1
    assert validated[0].validated is True


def test_validate_citations_not_matching():
    """Test validating citations that don't match retrieved chunks."""
    citations = [
        Citation(
            reference="ITA s.146(1)",
            text="RRSP definition",
            url=None,
            validated=False,
        ),
    ]

    retrieved = [
        SearchResult(
            chunk_id="ITA-118-001",
            text="Text about basic personal amount",
            metadata={"section": "118", "reference": "ITA s.118(1)"},
            score=0.95,
        ),
    ]

    validated = validate_citations(citations, retrieved)

    assert len(validated) == 1
    assert validated[0].validated is False


def test_validate_citations_loose_matching():
    """Test loose validation by section number."""
    citations = [
        Citation(
            reference="ITA s.118(1)(a)",
            text="Specific provision",
            url=None,
            validated=False,
        ),
    ]

    # Retrieved chunk only has section 118, not full subsection
    retrieved = [
        SearchResult(
            chunk_id="ITA-118-001",
            text="Text about section 118",
            metadata={"section": "118", "reference": "ITA s.118"},
            score=0.95,
        ),
    ]

    validated = validate_citations(citations, retrieved)

    # Should match based on section number (loose validation)
    assert len(validated) == 1
    assert validated[0].validated is True


def test_validate_citations_deduplication():
    """Test that duplicate citations are handled."""
    citations = [
        Citation("ITA s.118(1)", "Text 1", None, False),
        Citation("ITA s.118(1)", "Text 2", None, False),  # Duplicate
    ]

    retrieved = [
        SearchResult(
            "ITA-118-001",
            "Text",
            {"section": "118", "reference": "ITA s.118(1)"},
            0.95,
        ),
    ]

    validated = validate_citations(citations, retrieved)

    # Should handle duplicates gracefully
    assert len(validated) == 2


def test_generate_url_section_only():
    """Test URL generation for section-only reference."""
    url = generate_url("ITA s.118")

    assert "laws-lois.justice.gc.ca" in url
    assert "I-3.3" in url  # Income Tax Act
    assert "118" in url


def test_generate_url_with_subsection():
    """Test URL generation with subsection."""
    url = generate_url("ITA s.118(1)")

    assert "laws-lois.justice.gc.ca" in url
    assert "118" in url


def test_generate_url_invalid_reference():
    """Test URL generation with invalid reference."""
    # Should return None or placeholder for invalid references
    url = generate_url("Invalid reference")

    assert url is None or "laws-lois.justice.gc.ca" not in url


def test_extract_citations_with_quotes():
    """Test extraction preserves quoted text."""
    response = """The basic personal amount is defined.

Citations:
- ITA s.118(1): "For the purpose of computing the tax... there may be deducted the amount of..."
"""

    citations = extract_citations(response)

    assert len(citations) >= 1
    # Should preserve the quoted text
    assert any("there may be deducted" in c.text for c in citations)
