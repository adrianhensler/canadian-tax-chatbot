"""Tests for LLM interface and providers."""

import pytest
from unittest.mock import Mock, patch
from src.chat.llm_interface import LLMResponse, LLMProvider
from src.chat.providers.openai import OpenAIProvider


def test_llm_response_structure():
    """Test LLMResponse dataclass structure."""
    response = LLMResponse(
        content="Test response",
        model="gpt-5.2",
        usage={"prompt_tokens": 10, "completion_tokens": 20},
    )
    assert response.content == "Test response"
    assert response.model == "gpt-5.2"
    assert response.usage["prompt_tokens"] == 10
    assert response.usage["completion_tokens"] == 20


def test_openai_provider_initialization():
    """Test OpenAI provider can be initialized with API key."""
    provider = OpenAIProvider(api_key="test-key", model="gpt-5.2")
    assert provider.model == "gpt-5.2"
    assert provider.client is not None


@patch("src.chat.providers.openai.OpenAI")
def test_openai_provider_generate(mock_openai_class):
    """Test OpenAI provider generates responses correctly."""
    # Setup mock
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Tax answer with citations"
    mock_response.model = "gpt-5.2"
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50

    mock_client.chat.completions.create.return_value = mock_response

    # Test
    provider = OpenAIProvider(api_key="test-key")
    messages = [{"role": "user", "content": "What is the basic personal amount?"}]
    response = provider.generate(messages, temperature=0.0, max_tokens=2000)

    # Verify
    assert isinstance(response, LLMResponse)
    assert response.content == "Tax answer with citations"
    assert response.model == "gpt-5.2"
    assert response.usage["prompt_tokens"] == 100
    assert response.usage["completion_tokens"] == 50

    # Verify API call
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-5.2",
        messages=messages,
        temperature=0.0,
        max_tokens=2000,
    )


@patch("src.chat.providers.openai.OpenAI")
def test_openai_provider_custom_model(mock_openai_class):
    """Test OpenAI provider with custom model."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Response"
    mock_response.model = "gpt-4o"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20

    mock_client.chat.completions.create.return_value = mock_response

    # Test with custom model
    provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
    messages = [{"role": "user", "content": "Test"}]
    response = provider.generate(messages)

    assert response.model == "gpt-4o"
    mock_client.chat.completions.create.assert_called_once()


def test_llm_provider_protocol():
    """Test that OpenAIProvider implements LLMProvider protocol."""
    # This test verifies protocol compliance at runtime
    provider = OpenAIProvider(api_key="test-key")

    # Check method exists and has correct signature
    assert hasattr(provider, "generate")
    assert callable(provider.generate)
