#!/usr/bin/env python3
"""
Verify retrieval quality against eval questions.

Usage:
    python scripts/verify_retrieval.py
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.retriever import Retriever

EVAL_DIR = Path("eval/canadian-tax-qa-dataset")


def main():
    print("=" * 70)
    print("Retrieval Verification")
    print("=" * 70)

    # Initialize retriever
    try:
        retriever = Retriever(corpus_path=Path("data/corpus/current"))
    except ValueError as e:
        print(f"Error: {e}")
        print("Run ingestion first: python scripts/ingest_corpus.py")
        return 1

    print(f"Corpus loaded: {retriever._store.count()} chunks\n")

    total_correct = 0
    total_questions = 0

    # Test each question file
    for filename in ["basic_questions.jsonl", "tricky_questions.jsonl"]:
        filepath = EVAL_DIR / filename
        if not filepath.exists():
            print(f"Skipping {filename} (not found)")
            continue

        print(f"\n{filename}:")
        print("-" * 70)

        correct = 0
        total = 0

        with open(filepath) as f:
            for line in f:
                if not line.strip() or not line.startswith("{"):
                    continue

                q = json.loads(line)
                question = q["question"]
                expected = q.get("source_section", "")

                # Retrieve results
                results = retriever.retrieve(question, k=5)
                top_refs = [r.metadata.get("reference", "") for r in results[:3]]

                # Check if expected source is in top 3
                found = any(expected.lower() in ref.lower() for ref in top_refs)
                status = "PASS" if found else "FAIL"

                if found:
                    correct += 1
                total += 1

                print(f"  [{status}] {question[:60]}...")
                if not found:
                    print(f"       Expected: {expected}")
                    print(f"       Got: {top_refs}")

        recall = correct / total if total > 0 else 0
        print(f"\n  Recall: {correct}/{total} = {recall:.1%}")

        total_correct += correct
        total_questions += total

    print("\n" + "=" * 70)
    overall_recall = total_correct / total_questions if total_questions > 0 else 0
    print(f"Overall Recall: {total_correct}/{total_questions} = {overall_recall:.1%}")
    print("=" * 70)

    # Check against target
    if overall_recall >= 0.85:
        print("\n✓ SUCCESS: Retrieval recall meets 85% target")
        return 0
    else:
        print(f"\n✗ FAIL: Retrieval recall {overall_recall:.1%} below 85% target")
        return 1


if __name__ == "__main__":
    sys.exit(main())
