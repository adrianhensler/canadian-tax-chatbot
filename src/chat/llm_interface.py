"""LLM provider interface and response types."""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    usage: dict[str, int]  # tokens used (prompt_tokens, completion_tokens)


class LLMProvider(Protocol):
    """Protocol for LLM providers.

    Any class implementing this protocol can be used as an LLM provider
    for the chatbot. This allows swapping between OpenAI, Anthropic, local
    models, etc.
    """

    def generate(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with content, model name, and usage stats
        """
        ...
