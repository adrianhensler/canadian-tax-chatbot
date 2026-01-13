#!/usr/bin/env python3
"""
Evaluate chatbot against eval dataset.

Usage:
    OPENAI_API_KEY=sk-... python scripts/evaluate_chatbot.py
"""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chat.chatbot import Chatbot
from src.retrieval.retriever import Retriever
from src.chat.providers.openai import OpenAIProvider


EVAL_DIR = Path("eval/canadian-tax-qa-dataset")


def main():
    print("=" * 70)
    print("Chatbot Evaluation")
    print("=" * 70)

    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return 1

    # Initialize chatbot
    try:
        retriever = Retriever(corpus_path=Path("data/corpus/current"))
        llm = OpenAIProvider(api_key=api_key, model="gpt-5.2")
        chatbot = Chatbot(retriever, llm, k=5)
    except ValueError as e:
        print(f"Error: {e}")
        print("Run ingestion first: python scripts/ingest_corpus.py")
        return 1

    print(f"✓ Chatbot initialized")
    print(f"  Corpus: {retriever._store.count()} chunks")
    print(f"  LLM: {llm.model}\n")

    results = {
        "total_questions": 0,
        "citation_accuracy": 0.0,
        "hallucination_rate": 0.0,
        "refusal_accuracy": 0.0,
        "questions": [],
    }

    # Test each question file
    for filename in ["basic_questions.jsonl", "tricky_questions.jsonl", "should_refuse.jsonl"]:
        filepath = EVAL_DIR / filename
        if not filepath.exists():
            print(f"Skipping {filename} (not found)")
            continue

        print(f"\n{filename}:")
        print("-" * 70)

        with open(filepath) as f:
            for line in f:
                if not line.strip() or not line.startswith("{"):
                    continue

                q = json.loads(line)
                question = q["question"]
                expected_source = q.get("source_section", "")
                difficulty = q.get("difficulty", "unknown")

                print(f"\nQ: {question[:80]}...")

                # Get chatbot response
                response = chatbot.ask(question)

                # Evaluate citation accuracy
                citation_correct = evaluate_citations(
                    response, expected_source, difficulty == "should-refuse"
                )

                # Evaluate refusal accuracy (for should_refuse questions)
                refusal_correct = True
                if difficulty == "should-refuse":
                    refusal_correct = response.should_refuse

                # Check for hallucinations
                hallucination = detect_hallucination(response)

                # Print results
                print(f"  Answer: {response.answer[:100]}...")
                print(f"  Citations: {[c.reference for c in response.citations]}")
                print(f"  Validated: {[c.reference for c in response.citations if c.validated]}")
                print(f"  Should refuse: {response.should_refuse}")
                print(f"  ✓ Citation accuracy: {'PASS' if citation_correct else 'FAIL'}")
                if difficulty == "should-refuse":
                    print(f"  ✓ Refusal accuracy: {'PASS' if refusal_correct else 'FAIL'}")
                print(f"  ✓ Hallucination check: {'PASS' if not hallucination else 'FAIL'}")

                # Record results
                results["total_questions"] += 1
                results["questions"].append({
                    "question": question,
                    "expected_source": expected_source,
                    "citations": [c.reference for c in response.citations],
                    "validated_citations": [c.reference for c in response.citations if c.validated],
                    "citation_correct": citation_correct,
                    "refusal_correct": refusal_correct,
                    "hallucination": hallucination,
                    "difficulty": difficulty,
                })

    # Calculate metrics
    if results["total_questions"] > 0:
        citation_passes = sum(1 for q in results["questions"] if q["citation_correct"])
        results["citation_accuracy"] = citation_passes / results["total_questions"]

        hallucination_count = sum(1 for q in results["questions"] if q["hallucination"])
        results["hallucination_rate"] = hallucination_count / results["total_questions"]

        refusal_questions = [q for q in results["questions"] if q["difficulty"] == "should-refuse"]
        if refusal_questions:
            refusal_passes = sum(1 for q in refusal_questions if q["refusal_correct"])
            results["refusal_accuracy"] = refusal_passes / len(refusal_questions)

    # Print summary
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)
    print(f"Total questions: {results['total_questions']}")
    print(f"Citation accuracy: {results['citation_accuracy']:.1%} (target: ≥90%)")
    print(f"Hallucination rate: {results['hallucination_rate']:.1%} (target: ≤5%)")
    if results["refusal_accuracy"] > 0:
        print(f"Refusal accuracy: {results['refusal_accuracy']:.1%} (target: ≥90%)")
    print("=" * 70)

    # Check success criteria
    success = (
        results["citation_accuracy"] >= 0.90
        and results["hallucination_rate"] <= 0.05
        and (results["refusal_accuracy"] >= 0.90 or results["refusal_accuracy"] == 0)
    )

    if success:
        print("\n✓ SUCCESS: All metrics meet targets")
        return 0
    else:
        print("\n✗ FAIL: Some metrics below targets")
        return 1


def evaluate_citations(response, expected_source: str, is_refusal_question: bool) -> bool:
    """Evaluate if citations are correct.

    For refusal questions, no citations expected.
    For others, at least one validated citation expected.
    """
    if is_refusal_question:
        # Refusal questions don't need citations
        return True

    if not response.citations:
        return False

    # Check if any validated citations
    validated = [c for c in response.citations if c.validated]

    return len(validated) > 0


def detect_hallucination(response) -> bool:
    """Detect if response contains hallucinated citations.

    A hallucination is a citation that was not validated against retrieved context.
    """
    if not response.citations:
        return False

    # Check for unvalidated citations (potential hallucinations)
    unvalidated = [c for c in response.citations if not c.validated]

    # If more than half citations are unvalidated, likely hallucination
    if unvalidated and len(unvalidated) > len(response.citations) / 2:
        return True

    return False


if __name__ == "__main__":
    sys.exit(main())
