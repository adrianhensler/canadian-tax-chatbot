"""Section-aware chunking for ITA documents"""

from dataclasses import dataclass, field
from typing import Any
import tiktoken
import hashlib

from .xml_parser import Section, Subsection


@dataclass
class Chunk:
    """A chunk of text with metadata for embedding"""

    text: str
    chunk_id: str
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


def chunk_section(
    section: Section,
    max_tokens: int = 1500,
    overlap_tokens: int = 200,
) -> list[Chunk]:
    """
    Chunk a section respecting ITA structure.

    Strategy:
    1. If entire section fits in max_tokens, return as single chunk
    2. Otherwise, split at subsection boundaries
    3. If subsection still too large, truncate (simplified for now)
    4. Add overlap between chunks (future enhancement)

    Args:
        section: Parsed Section object
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Overlap between chunks (not yet implemented)

    Returns:
        List of Chunk objects with metadata
    """
    encoder = tiktoken.get_encoding("cl100k_base")

    full_text = section.get_full_text()
    full_tokens = len(encoder.encode(full_text))

    base_metadata = {
        "source": "Income Tax Act",
        "source_abbreviation": "ITA",
        "section": section.section_number,
        "title": section.marginal_note,
        "reference": section.get_reference(),
        "document_type": "federal_statute",
    }

    if full_tokens <= max_tokens:
        # Section fits in one chunk
        chunk_id = _generate_chunk_id("ITA", section.section_number, "", 0, full_text)
        return [
            Chunk(
                text=full_text,
                chunk_id=chunk_id,
                token_count=full_tokens,
                metadata={**base_metadata, "type": "section"},
            )
        ]

    # Split at subsection level
    chunks = []
    for i, subsection in enumerate(section.subsections):
        ss_chunk = _chunk_subsection(subsection, section, i, max_tokens, encoder)
        if ss_chunk:
            chunks.append(ss_chunk)

    return chunks


def _chunk_subsection(
    subsection: Subsection,
    parent: Section,
    index: int,
    max_tokens: int,
    encoder,
) -> Chunk:
    """Chunk a subsection"""
    # Build subsection text with structure
    ss_text = f"({subsection.label}) {subsection.text}"
    for p in subsection.paragraphs:
        ss_text += f"\n  ({p.label}) {p.text}"
        for sp in p.subparagraphs:
            ss_text += f"\n    ({sp.label}) {sp.text}"

    ss_tokens = len(encoder.encode(ss_text))

    metadata = {
        "source": "Income Tax Act",
        "source_abbreviation": "ITA",
        "section": parent.section_number,
        "subsection": subsection.label,
        "title": parent.marginal_note,
        "reference": f"ITA s.{parent.section_number}({subsection.label})",
        "document_type": "federal_statute",
        "type": "subsection",
    }

    # If subsection is too large, truncate (simplified approach)
    if ss_tokens > max_tokens:
        # Truncate text to approximate token limit
        # Rough estimate: 1 token ≈ 4 characters
        char_limit = max_tokens * 4
        ss_text = ss_text[:char_limit]
        ss_tokens = len(encoder.encode(ss_text))
        metadata["truncated"] = True

    chunk_id = _generate_chunk_id("ITA", parent.section_number, subsection.label, index, ss_text)

    return Chunk(
        text=ss_text,
        chunk_id=chunk_id,
        token_count=ss_tokens,
        metadata=metadata,
    )


def _generate_chunk_id(source: str, section: str, subsection: str, index: int, text: str) -> str:
    """Generate unique chunk ID"""
    # Create hash of text to ensure uniqueness even for empty section numbers
    text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    section_id = section if section else "unknown"
    subsection_id = f"-{subsection}" if subsection else ""
    return f"{source}-{section_id}{subsection_id}-{index:03d}-{text_hash}"
