"""OpenAI LLM provider implementation."""

from openai import OpenAI
from ..llm_interface import LLMResponse


class OpenAIProvider:
    """OpenAI GPT provider for chat completions."""

    def __init__(self, api_key: str, model: str = "gpt-5.2"):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-5.2)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate a response using OpenAI API.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with content, model name, and usage stats
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
        )
