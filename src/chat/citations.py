"""Citation extraction and validation for tax answers."""

import re
from dataclasses import dataclass
from src.retrieval.vector_store import SearchResult


@dataclass
class Citation:
    """A citation to an ITA section or CRA source."""

    reference: str  # "ITA s.118(1)"
    text: str  # Quoted supporting text
    url: str | None  # Link to Justice Laws
    validated: bool  # Was this in retrieved context?


def extract_citations(response_text: str) -> list[Citation]:
    """Parse citations from LLM response.

    Looks for:
    1. Formatted citations block: "Citations:\\n- ITA s.XXX: \\"text\\""
    2. Inline citations: "According to ITA s.XXX, ..."

    Args:
        response_text: LLM response text

    Returns:
        List of Citation objects
    """
    citations = []

    # Pattern 1: Extract from formatted citations block
    # Matches: - ITA s.XXX: "quoted text" or - ITA s.XXX(Y)(z): "quoted text"
    citation_block_pattern = r'-\s*(ITA\s+s\.\d+(?:\(\d+\))?(?:\([a-z]\))?)\s*:\s*["\']([^"\']+)["\']'
    matches = re.findall(citation_block_pattern, response_text, re.IGNORECASE)

    for reference, text in matches:
        citations.append(
            Citation(
                reference=reference,
                text=text.strip(),
                url=generate_url(reference),
                validated=False,
            )
        )

    # Pattern 2: Extract inline citations
    # Matches: ITA s.XXX or ITA s.XXX(Y) or ITA s.XXX(Y)(z)
    inline_pattern = r'ITA\s+s\.(\d+(?:\(\d+\))?(?:\([a-z]\))?)'
    inline_matches = re.findall(inline_pattern, response_text, re.IGNORECASE)

    for section_ref in inline_matches:
        reference = f"ITA s.{section_ref}"

        # Only add if not already in citations from block
        if not any(c.reference == reference for c in citations):
            citations.append(
                Citation(
                    reference=reference,
                    text="",  # No quoted text for inline citations
                    url=generate_url(reference),
                    validated=False,
                )
            )

    # Pattern 3: Extract "Section XXX" format
    section_only_pattern = r'\bSection\s+(\d+(?:\(\d+\))?(?:\([a-z]\))?)\b'
    section_matches = re.findall(section_only_pattern, response_text)

    for section_ref in section_matches:
        reference = f"ITA s.{section_ref}"

        # Only add if not already in citations
        if not any(c.reference == reference for c in citations):
            citations.append(
                Citation(
                    reference=reference,
                    text="",
                    url=generate_url(reference),
                    validated=False,
                )
            )

    return citations


def validate_citations(
    citations: list[Citation], retrieved: list[SearchResult]
) -> list[Citation]:
    """Mark citations as validated if they match retrieved chunks.

    Uses loose validation: citation is valid if section number appears
    in any retrieved chunk's metadata.

    Args:
        citations: List of citations to validate
        retrieved: List of search results from retrieval

    Returns:
        List of citations with validated field updated
    """
    # Extract section numbers from retrieved chunks
    retrieved_sections = set()
    for result in retrieved:
        section = result.metadata.get("section", "")
        reference = result.metadata.get("reference", "")

        if section:
            retrieved_sections.add(section)

        # Also extract section from full reference
        if reference:
            match = re.search(r"s\.(\d+)", reference)
            if match:
                retrieved_sections.add(match.group(1))

    # Validate each citation
    validated = []
    for citation in citations:
        # Extract section number from citation reference
        match = re.search(r"s\.(\d+)", citation.reference)
        if match:
            section_num = match.group(1)
            citation.validated = section_num in retrieved_sections
        else:
            citation.validated = False

        validated.append(citation)

    return validated


def generate_url(reference: str) -> str | None:
    """Generate Justice Laws URL for ITA reference.

    Args:
        reference: ITA reference like "ITA s.118" or "ITA s.146(1)"

    Returns:
        URL to Justice Laws website, or None if invalid reference
    """
    # Extract section number
    match = re.search(r"s\.(\d+)", reference)
    if not match:
        return None

    section_num = match.group(1)

    # Generate URL to section
    # Note: Justice Laws URLs use format /section-XXX.html
    base_url = "https://laws-lois.justice.gc.ca/eng/acts/I-3.3"
    url = f"{base_url}/section-{section_num}.html"

    return url
