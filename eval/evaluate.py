"""
Evaluation script for the Northwind RAG pipeline.

Runs every question in eval/golden_set.jsonl through the full
pipeline (hybrid search -> rerank -> generate) and scores:

  1. Retrieval Hit Rate  -- did the correct source appear in top 5?
  2. Faithfulness        -- does the answer contain expected facts?

Exits with code 1 if overall score drops below PASS_THRESHOLD.
This exit code is what causes a GitHub Actions CI build to fail.

Usage:
    python eval/evaluate.py
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

# pyrefly: ignore [missing-import]
from retrieve import hybrid_search
# pyrefly: ignore [missing-import]
from rerank import rerank
# pyrefly: ignore [missing-import]
from generate import generate_answer, check_confidence

GOLDEN_SET   = ROOT / "eval" / "golden_set.jsonl"
PASS_THRESHOLD = 0.75
SLEEP_BETWEEN  = 2

def score_retrieval(chunks: list[dict], source_file: str) -> float:
    if source_file is None:
        return 1.0
    for chunk in chunks:
        chunk_source = chunk["metadata"]["source_file"]
        chunk_source = chunk_source.replace("\\", "/")
        if source_file in chunk_source:
            return 1.0
    return 0.0


def score_faithfulness(answer: str, expected_facts: list[str]) -> float:
    if not expected_facts:
        return 1.0
    answer_lower = answer.lower()
    hits = sum(
        1 for fact in expected_facts
        if fact.lower() in answer_lower
    )
    return hits / len(expected_facts)
def run_evaluation() -> dict:
    questions = []
    with open(GOLDEN_SET, "r") as f:
        for line in f:
            questions.append(json.loads(line))

    results = []
    for i, q in enumerate(questions, start=1):
        print(f"[{i:02d}/{len(questions)}] {q['category']:15s} | {q['question'][:55]}...")

        try:
            candidates = hybrid_search(q["question"], k=10)
            chunks     = rerank(q["question"], candidates, top_n=5)
            answer     = generate_answer(q["question"], chunks)

            ret_score  = score_retrieval(chunks, q["source_file"])
            faith_score = score_faithfulness(answer, q["expected_facts"])
            passed     = (ret_score + faith_score) / 2 >= 0.5

            results.append({
                "id"           : q["id"],
                "category"     : q["category"],
                "question"     : q["question"],
                "answer"       : answer,
                "ret_score"    : ret_score,
                "faith_score"  : faith_score,
                "passed"       : passed,
            })

            status = "✓" if passed else "✗"
            print(f"         {status} ret={ret_score:.1f} "
                  f"faith={faith_score:.2f}")

        except Exception as e:
            print(f"         ERROR: {e}")
            results.append({
                "id"          : q["id"],
                "category"    : q["category"],
                "question"    : q["question"],
                "answer"      : "",
                "ret_score"   : 0.0,
                "faith_score" : 0.0,
                "passed"      : False,
            })

        time.sleep(SLEEP_BETWEEN)

    return results


def print_report(results: list[dict]) -> float:
    print("\n" + "=" * 65)
    print("EVALUATION REPORT")
    print("=" * 65)

    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)

    for cat, items in categories.items():
        avg_ret   = sum(r["ret_score"]   for r in items) / len(items)
        avg_faith = sum(r["faith_score"] for r in items) / len(items)
        passed    = sum(1 for r in items if r["passed"])
        print(f"\n{cat.upper()} ({len(items)} questions)")
        print(f"  retrieval hit rate : {avg_ret:.2f}")
        print(f"  faithfulness       : {avg_faith:.2f}")
        print(f"  passed             : {passed}/{len(items)}")

    overall_ret   = sum(r["ret_score"]   for r in results) / len(results)
    overall_faith = sum(r["faith_score"] for r in results) / len(results)
    overall_score = (overall_ret + overall_faith) / 2

    print("\n" + "=" * 65)
    print(f"OVERALL RETRIEVAL HIT RATE : {overall_ret:.2f}")
    print(f"OVERALL FAITHFULNESS       : {overall_faith:.2f}")
    print(f"OVERALL SCORE              : {overall_score:.2f}")
    print(f"PASS THRESHOLD             : {PASS_THRESHOLD}")
    print(f"RESULT: {'PASS ✓' if overall_score >= PASS_THRESHOLD else 'FAIL ✗'}")
    print("=" * 65)

    return overall_score


def main():
    print("Starting evaluation...")
    print(f"Questions : {GOLDEN_SET.name}")
    print(f"Threshold : {PASS_THRESHOLD}\n")

    results = run_evaluation()
    overall_score = print_report(results)

    report_path = ROOT / "eval" / "last_report.jsonl"
    with open(report_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nDetailed report saved to: {report_path}")

    sys.exit(0 if overall_score >= PASS_THRESHOLD else 1)


if __name__ == "__main__":
    main()