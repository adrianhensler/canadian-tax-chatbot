"""Tests for prompt engineering and context formatting."""

import pytest
from src.chat.prompts import (
    SYSTEM_PROMPT,
    format_context,
    build_messages,
)
from src.retrieval.vector_store import SearchResult


def test_system_prompt_exists():
    """Test that SYSTEM_PROMPT is defined and non-empty."""
    assert SYSTEM_PROMPT is not None
    assert len(SYSTEM_PROMPT) > 0
    assert isinstance(SYSTEM_PROMPT, str)


def test_system_prompt_contains_citation_requirements():
    """Test that SYSTEM_PROMPT includes citation requirements."""
    assert "cite" in SYSTEM_PROMPT.lower()
    assert "ITA" in SYSTEM_PROMPT or "section" in SYSTEM_PROMPT.lower()


def test_system_prompt_contains_refusal_guidance():
    """Test that SYSTEM_PROMPT includes refusal behavior guidance."""
    prompt_lower = SYSTEM_PROMPT.lower()
    assert any(
        phrase in prompt_lower
        for phrase in ["don't know", "don't have information", "professional"]
    )


def test_format_context_single_result():
    """Test formatting a single search result."""
    result = SearchResult(
        chunk_id="ITA-118-001",
        text="The basic personal amount is a non-refundable tax credit available to all residents.",
        metadata={
            "section": "118",
            "subsection": "1",
            "reference": "ITA s.118(1)",
            "title": "Personal credits",
        },
        score=0.95,
    )

    context = format_context([result])

    assert "ITA s.118(1)" in context
    assert "Personal credits" in context
    assert "basic personal amount" in context


def test_format_context_multiple_results():
    """Test formatting multiple search results."""
    results = [
        SearchResult(
            chunk_id="ITA-118-001",
            text="Text about basic personal amount.",
            metadata={"section": "118", "reference": "ITA s.118(1)", "title": "Personal credits"},
            score=0.95,
        ),
        SearchResult(
            chunk_id="ITA-146-001",
            text="Text about RRSP contributions.",
            metadata={"section": "146", "reference": "ITA s.146(1)", "title": "RRSP"},
            score=0.90,
        ),
    ]

    context = format_context(results)

    assert "ITA s.118(1)" in context
    assert "ITA s.146(1)" in context
    assert "basic personal amount" in context
    assert "RRSP contributions" in context


def test_format_context_preserves_metadata():
    """Test that context formatting includes section references and titles."""
    result = SearchResult(
        chunk_id="ITA-248-001",
        text="Definition of 'property'.",
        metadata={
            "section": "248",
            "subsection": "1",
            "reference": "ITA s.248(1)",
            "title": "Definitions",
        },
        score=0.85,
    )

    context = format_context([result])

    # Should include reference for citation
    assert "ITA s.248(1)" in context
    # Should include title for context
    assert "Definitions" in context


def test_build_messages_structure():
    """Test that build_messages returns correct message structure."""
    question = "What is the basic personal amount?"
    context = "[Context 1] ITA s.118(1): Basic personal amount text..."

    messages = build_messages(question, context)

    assert isinstance(messages, list)
    assert len(messages) >= 2  # At least system and user message

    # First message should be system
    assert messages[0]["role"] == "system"
    assert "content" in messages[0]

    # Last message should be user question
    assert messages[-1]["role"] == "user"
    assert question in messages[-1]["content"]


def test_build_messages_includes_system_prompt():
    """Test that build_messages includes the system prompt."""
    question = "Test question"
    context = "Test context"

    messages = build_messages(question, context)

    system_message = messages[0]
    assert system_message["role"] == "system"
    assert "cite" in system_message["content"].lower()


def test_build_messages_includes_context():
    """Test that build_messages includes the retrieved context."""
    question = "What is the basic personal amount?"
    context = "[Context 1] ITA s.118(1): The basic personal amount..."

    messages = build_messages(question, context)

    # Context should be in user message or separate context message
    message_content = " ".join(msg["content"] for msg in messages)
    assert "ITA s.118(1)" in message_content
    assert "basic personal amount" in message_content.lower()


def test_format_context_empty_list():
    """Test formatting with no search results."""
    context = format_context([])

    # Should return empty string or placeholder
    assert isinstance(context, str)
    assert len(context) >= 0


def test_format_context_handles_missing_metadata():
    """Test formatting when metadata is incomplete."""
    result = SearchResult(
        chunk_id="ITA-unknown-001",
        text="Some tax text without full metadata.",
        metadata={},  # Empty metadata
        score=0.80,
    )

    # Should not crash
    context = format_context([result])
    assert isinstance(context, str)
    assert "tax text" in context
