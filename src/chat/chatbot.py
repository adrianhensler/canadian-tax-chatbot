"""Chatbot orchestration for tax Q&A."""

from dataclasses import dataclass
from src.retrieval.retriever import Retriever
from src.retrieval.vector_store import SearchResult
from .llm_interface import LLMProvider
from .prompts import format_context, build_messages
from .citations import Citation, extract_citations, validate_citations


@dataclass
class ChatResponse:
    """Response from the chatbot."""

    answer: str
    citations: list[Citation]
    retrieved_chunks: list[SearchResult]
    should_refuse: bool
    refusal_reason: str | None
    model: str
    usage: dict[str, int]


class Chatbot:
    """Tax chatbot with RAG pipeline."""

    def __init__(
        self,
        retriever: Retriever,
        llm_provider: LLMProvider,
        k: int = 5,
    ):
        """Initialize chatbot.

        Args:
            retriever: Retriever for finding relevant ITA sections
            llm_provider: LLM provider for generating answers
            k: Number of chunks to retrieve
        """
        self.retriever = retriever
        self.llm = llm_provider
        self.k = k

    def ask(self, question: str) -> ChatResponse:
        """Answer a tax question using RAG pipeline.

        Pipeline:
        1. Retrieve relevant chunks from ITA corpus
        2. Format context for LLM prompt
        3. Generate answer using LLM
        4. Extract and validate citations
        5. Detect refusal cases

        Args:
            question: User's tax question

        Returns:
            ChatResponse with answer, citations, and metadata
        """
        # 1. Retrieve relevant chunks
        results = self.retriever.retrieve(question, k=self.k)

        # 2. Format context
        context = format_context(results)

        # 3. Build prompt messages
        messages = build_messages(question, context)

        # 4. Generate response from LLM
        llm_response = self.llm.generate(messages)

        # 5. Extract citations
        citations = extract_citations(llm_response.content)

        # 6. Validate citations against retrieved chunks
        citations = validate_citations(citations, results)

        # 7. Detect refusal
        should_refuse, refusal_reason = detect_refusal(llm_response.content)

        return ChatResponse(
            answer=llm_response.content,
            citations=citations,
            retrieved_chunks=results,
            should_refuse=should_refuse,
            refusal_reason=refusal_reason,
            model=llm_response.model,
            usage=llm_response.usage,
        )


def detect_refusal(response_text: str) -> tuple[bool, str | None]:
    """Detect if the response is a refusal to answer.

    Args:
        response_text: LLM response text

    Returns:
        Tuple of (should_refuse, refusal_reason)
    """
    refusal_keywords = [
        "consult a tax professional",
        "consult a qualified",
        "I don't have information",
        "beyond the scope",
        "seek professional advice",
        "recommend consulting",
    ]

    text_lower = response_text.lower()

    for keyword in refusal_keywords:
        if keyword in text_lower:
            return True, f"Response contains refusal keyword: '{keyword}'"

    return False, None
