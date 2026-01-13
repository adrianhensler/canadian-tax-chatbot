#!/usr/bin/env python3
"""
Canadian Tax Chatbot CLI

Ask questions about Canadian income tax and get answers with citations
to the Income Tax Act.

Usage:
    python scripts/cli.py "What is the basic personal amount?"
    python scripts/cli.py --interactive
    OPENAI_API_KEY=sk-... python scripts/cli.py "question"

Examples:
    # Single question
    python scripts/cli.py "What are RRSP contribution limits?"

    # Interactive mode
    python scripts/cli.py -i

    # JSON output for scripting
    python scripts/cli.py "What is TFSA?" --json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chat.chatbot import Chatbot, ChatResponse
from src.retrieval.retriever import Retriever
from src.chat.providers.openai import OpenAIProvider


def main():
    parser = argparse.ArgumentParser(
        description="Canadian Tax Chatbot - Ask questions about Canadian income tax",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "What is the basic personal amount?"
  %(prog)s --interactive
  %(prog)s "What is RRSP?" --json
  %(prog)s "What is TFSA?" -v

Environment:
  OPENAI_API_KEY    OpenAI API key (required)
        """,
    )
    parser.add_argument("question", nargs="?", help="Tax question to answer")
    parser.add_argument(
        "-i", "--interactive", action="store_true", help="Interactive chat mode"
    )
    parser.add_argument("--model", default="gpt-5.2", help="LLM model (default: gpt-5.2)")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("data/corpus/current"),
        help="Corpus path (default: data/corpus/current)",
    )
    parser.add_argument(
        "-k", type=int, default=5, help="Number of chunks to retrieve (default: 5)"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show retrieved chunks"
    )
    parser.add_argument(
        "--no-citations", action="store_true", help="Hide citation details"
    )
    args = parser.parse_args()

    # Validate arguments
    if not args.interactive and not args.question:
        parser.error("Question required (or use --interactive)")

    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=sk-...")
        return 1

    # Initialize chatbot
    try:
        retriever = Retriever(corpus_path=args.corpus)
        llm = OpenAIProvider(api_key=api_key, model=args.model)
        chatbot = Chatbot(retriever, llm, k=args.k)
    except ValueError as e:
        print(f"Error: {e}")
        print("Run ingestion first: python scripts/ingest_corpus.py --download")
        return 1

    # Run mode
    if args.interactive:
        return run_interactive(chatbot, args)
    else:
        return run_single(chatbot, args.question, args)


def run_single(chatbot: Chatbot, question: str, args) -> int:
    """Run single question mode."""
    response = chatbot.ask(question)

    if args.json:
        print_json(question, response)
    else:
        print_formatted(question, response, args)

    return 0


def run_interactive(chatbot: Chatbot, args) -> int:
    """Run interactive mode."""
    print_header()
    print("Type your tax questions. Enter 'quit', 'exit', or Ctrl+C to stop.\n")

    while True:
        try:
            question = input("You: ").strip()
            if not question:
                continue
            if question.lower() in ("quit", "exit", "q"):
                print("\nGoodbye!")
                break

            print("\nThinking...", end="\r")
            response = chatbot.ask(question)
            print(" " * 20, end="\r")  # Clear "Thinking..."
            print_formatted(question, response, args, interactive=True)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

    return 0


def print_header():
    """Print CLI header."""
    print("=" * 80)
    print("CANADIAN TAX CHATBOT")
    print("=" * 80)


def print_formatted(
    question: str, response: ChatResponse, args, interactive: bool = False
):
    """Print formatted response."""
    if not interactive:
        print_header()
        print(f"\nQuestion: {question}\n")

    # Answer
    print(f"\nAnswer:\n{response.answer}\n")

    # Citations
    if not args.no_citations and response.citations:
        print("Citations:")
        for c in response.citations:
            status = "✓" if c.validated else "○"
            print(f"  {status} {c.reference}")
            if c.url:
                print(f"    {c.url}")
        print()

    # Verbose: show retrieved chunks
    if args.verbose:
        print(f"Retrieved {len(response.retrieved_chunks)} chunks:")
        for chunk in response.retrieved_chunks[:3]:
            ref = chunk.metadata.get("reference", "unknown")
            text_preview = chunk.text[:80].replace("\n", " ")
            print(f"  - {ref}: {text_preview}...")
        if len(response.retrieved_chunks) > 3:
            print(f"  ... and {len(response.retrieved_chunks) - 3} more")
        print()

    # Footer (single question mode only)
    if not interactive:
        prompt_tokens = response.usage.get("prompt_tokens", 0)
        completion_tokens = response.usage.get("completion_tokens", 0)
        print(
            f"Model: {response.model} | Tokens: {prompt_tokens} prompt, {completion_tokens} completion"
        )
        print("=" * 80)


def print_json(question: str, response: ChatResponse):
    """Print JSON output."""
    output = {
        "question": question,
        "answer": response.answer,
        "citations": [
            {
                "reference": c.reference,
                "text": c.text,
                "url": c.url,
                "validated": c.validated,
            }
            for c in response.citations
        ],
        "should_refuse": response.should_refuse,
        "refusal_reason": response.refusal_reason,
        "model": response.model,
        "usage": response.usage,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    sys.exit(main())
