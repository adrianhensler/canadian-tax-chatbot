"""Prompt engineering and context formatting for tax chatbot."""

from src.retrieval.vector_store import SearchResult


SYSTEM_PROMPT = """You are a Canadian tax assistant. Answer questions using ONLY the provided context from the Income Tax Act and CRA guidance.

RULES:
1. Cite every claim with the section reference (e.g., "ITA s.118(1)")
2. If the context doesn't contain the answer, say "I don't have information about that in the provided context"
3. Never invent tax rules or numbers not in the context
4. For complex situations requiring professional judgment, recommend consulting a tax professional
5. Never perform tax calculations - only explain rules

OUTPUT FORMAT:
Provide your answer, then list citations in this format:
Citations:
- ITA s.XXX: "quoted text supporting claim"
- ITA s.YYY: "quoted text supporting claim"
"""


def format_context(results: list[SearchResult]) -> str:
    """Format retrieved chunks for prompt injection.

    Args:
        results: List of search results from retriever

    Returns:
        Formatted context string with section references and text
    """
    if not results:
        return ""

    formatted_chunks = []
    for i, result in enumerate(results, 1):
        # Extract metadata
        reference = result.metadata.get("reference", "Unknown")
        title = result.metadata.get("title", "")

        # Format chunk with reference and title
        chunk_text = f"[Context {i}] {reference}"
        if title:
            chunk_text += f" - {title}"
        chunk_text += f"\n{result.text}\n"

        formatted_chunks.append(chunk_text)

    return "\n".join(formatted_chunks)


def build_messages(question: str, context: str) -> list[dict]:
    """Build message array for LLM API.

    Args:
        question: User's tax question
        context: Formatted context from retrieved chunks

    Returns:
        List of message dicts with 'role' and 'content' keys
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Context from Income Tax Act:

{context}

Question: {question}

Please answer the question using only the provided context. Include citations to specific ITA sections.""",
        },
    ]

    return messages
