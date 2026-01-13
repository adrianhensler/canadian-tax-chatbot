"""Tests for chatbot orchestration."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.chat.chatbot import Chatbot, ChatResponse
from src.chat.llm_interface import LLMResponse
from src.chat.citations import Citation
from src.retrieval.vector_store import SearchResult


@pytest.fixture
def mock_retriever():
    """Create a mock retriever."""
    retriever = Mock()
    retriever.retrieve.return_value = [
        SearchResult(
            chunk_id="ITA-118-001",
            text="The basic personal amount is a non-refundable tax credit available to all residents.",
            metadata={
                "section": "118",
                "subsection": "1",
                "reference": "ITA s.118(1)",
                "title": "Personal credits",
            },
            score=0.95,
        ),
    ]
    return retriever


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    llm = Mock()
    llm.generate.return_value = LLMResponse(
        content="""The basic personal amount for 2024 is $15,705. This is a non-refundable tax credit available to all Canadian residents.

Citations:
- ITA s.118(1): "For the purpose of computing the tax... there may be deducted the basic personal amount"
""",
        model="gpt-5.2",
        usage={"prompt_tokens": 100, "completion_tokens": 50},
    )
    return llm


def test_chatbot_initialization(mock_retriever, mock_llm):
    """Test chatbot can be initialized."""
    bot = Chatbot(mock_retriever, mock_llm, k=5)

    assert bot.retriever == mock_retriever
    assert bot.llm == mock_llm
    assert bot.k == 5


def test_chatbot_ask_returns_chat_response(mock_retriever, mock_llm):
    """Test chatbot.ask() returns ChatResponse."""
    bot = Chatbot(mock_retriever, mock_llm)
    response = bot.ask("What is the basic personal amount?")

    assert isinstance(response, ChatResponse)
    assert isinstance(response.answer, str)
    assert isinstance(response.citations, list)
    assert isinstance(response.retrieved_chunks, list)
    assert isinstance(response.should_refuse, bool)
    assert isinstance(response.model, str)
    assert isinstance(response.usage, dict)


def test_chatbot_calls_retriever(mock_retriever, mock_llm):
    """Test that chatbot calls retriever with query."""
    bot = Chatbot(mock_retriever, mock_llm, k=5)
    question = "What is the basic personal amount?"

    bot.ask(question)

    mock_retriever.retrieve.assert_called_once_with(question, k=5)


def test_chatbot_calls_llm_with_context(mock_retriever, mock_llm):
    """Test that chatbot calls LLM with formatted context."""
    bot = Chatbot(mock_retriever, mock_llm)
    question = "What is the basic personal amount?"

    bot.ask(question)

    # Verify LLM was called
    mock_llm.generate.assert_called_once()

    # Verify messages structure
    call_args = mock_llm.generate.call_args
    messages = call_args[0][0]  # First positional argument

    assert isinstance(messages, list)
    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"

    # Verify context is included
    user_message = messages[-1]["content"]
    assert "ITA s.118(1)" in user_message
    assert question in user_message


def test_chatbot_extracts_citations(mock_retriever, mock_llm):
    """Test that chatbot extracts citations from LLM response."""
    bot = Chatbot(mock_retriever, mock_llm)
    response = bot.ask("What is the basic personal amount?")

    assert len(response.citations) > 0
    assert any("118" in c.reference for c in response.citations)


def test_chatbot_validates_citations(mock_retriever, mock_llm):
    """Test that chatbot validates citations against retrieved chunks."""
    bot = Chatbot(mock_retriever, mock_llm)
    response = bot.ask("What is the basic personal amount?")

    # Citation should be validated because section 118 was retrieved
    assert len(response.citations) > 0
    validated_citations = [c for c in response.citations if c.validated]
    assert len(validated_citations) > 0


def test_chatbot_detects_refusal(mock_retriever):
    """Test that chatbot detects refusal responses."""
    llm = Mock()
    llm.generate.return_value = LLMResponse(
        content="This question involves complex tax planning. I recommend consulting a qualified tax professional.",
        model="gpt-5.2",
        usage={"prompt_tokens": 50, "completion_tokens": 20},
    )

    bot = Chatbot(mock_retriever, llm)
    response = bot.ask("Complex tax planning question?")

    assert response.should_refuse is True
    assert response.refusal_reason is not None


def test_chatbot_handles_no_context(mock_retriever):
    """Test chatbot handles case where retriever returns no results."""
    mock_retriever.retrieve.return_value = []

    llm = Mock()
    llm.generate.return_value = LLMResponse(
        content="I don't have information about that in the provided context.",
        model="gpt-5.2",
        usage={"prompt_tokens": 50, "completion_tokens": 10},
    )

    bot = Chatbot(mock_retriever, llm)
    response = bot.ask("Unknown question?")

    # Should still return valid response
    assert isinstance(response, ChatResponse)
    assert len(response.citations) == 0


def test_chatbot_includes_retrieved_chunks(mock_retriever, mock_llm):
    """Test that response includes the retrieved chunks."""
    bot = Chatbot(mock_retriever, mock_llm)
    response = bot.ask("What is the basic personal amount?")

    assert len(response.retrieved_chunks) > 0
    assert all(isinstance(c, SearchResult) for c in response.retrieved_chunks)


def test_chatbot_includes_model_info(mock_retriever, mock_llm):
    """Test that response includes model name and usage stats."""
    bot = Chatbot(mock_retriever, mock_llm)
    response = bot.ask("What is the basic personal amount?")

    assert response.model == "gpt-5.2"
    assert "prompt_tokens" in response.usage
    assert "completion_tokens" in response.usage


def test_chat_response_dataclass():
    """Test ChatResponse dataclass structure."""
    response = ChatResponse(
        answer="Test answer",
        citations=[],
        retrieved_chunks=[],
        should_refuse=False,
        refusal_reason=None,
        model="gpt-5.2",
        usage={"prompt_tokens": 10, "completion_tokens": 20},
    )

    assert response.answer == "Test answer"
    assert response.citations == []
    assert response.should_refuse is False


def test_chatbot_custom_k_value(mock_retriever, mock_llm):
    """Test that chatbot respects custom k value."""
    bot = Chatbot(mock_retriever, mock_llm, k=10)

    bot.ask("Test question")

    mock_retriever.retrieve.assert_called_once_with("Test question", k=10)
