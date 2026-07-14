"""

RAGAS evaluation for the RAG Citation Engine.
Uses RAGAS 0.2.x API with Gemini as the judge LLM.

Usage:
    python eval/evaluate_ragas.py

    
"""
import os
import sys
import json
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from retrieve import hybrid_search
from rerank import rerank
from generate import generate_answer

from ragas import evaluate, EvaluationDataset
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    LLMContextPrecisionWithoutReference,
    Faithfulness,
    ResponseRelevancy,
)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

GOLDEN_SET   = ROOT / "eval" / "golden_set.jsonl"
SAMPLE_SIZE  = 5
SLEEP_BETWEEN = 10


def load_questions(path: Path, limit: int) -> list[dict]:
    questions = []
    with open(path) as f:
        for line in f:
            q = json.loads(line)
            if q["source_file"] is not None:
                questions.append(q)
            if len(questions) >= limit:
                break
    return questions


def run_pipeline(question: str) -> tuple[str, list[str]]:
    candidates = hybrid_search(question, k=10)
    chunks     = rerank(question, candidates, top_n=5)
    answer     = generate_answer(question, chunks)
    contexts   = [c["text"] for c in chunks]
    return answer, contexts


def main():
    print("Loading questions...")
    questions = load_questions(GOLDEN_SET, SAMPLE_SIZE)
    print(f"Loaded {len(questions)} questions\n")

    # ── run pipeline on each question ─────────────────────────
    samples = []
    for i, q in enumerate(questions, start=1):
        print(f"[{i:02d}/{len(questions)}] {q['question'][:60]}...")
        try:
            answer, contexts = run_pipeline(q["question"])
            samples.append({
                "user_input"  : q["question"],
                "response"    : answer,
                "retrieved_contexts": contexts,
            })
            print(f"         ✓ {answer[:80]}...")
        except Exception as e:
            print(f"         ✗ ERROR: {e}")
        time.sleep(SLEEP_BETWEEN)

    # ── build RAGAS dataset ───────────────────────────────────
    dataset = EvaluationDataset.from_list(samples)

    # ── set up Gemini as judge ────────────────────────────────
    print("\nSetting up Gemini judge...")
    gemini_llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )
    gemini_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )

    llm        = LangchainLLMWrapper(gemini_llm)
    embeddings = LangchainEmbeddingsWrapper(gemini_embeddings)

    # ── evaluate ──────────────────────────────────────────────
    print("Running RAGAS evaluation...\n")
    result = evaluate(
        dataset=dataset,
        metrics=[
            LLMContextPrecisionWithoutReference(),
            Faithfulness(),
            ResponseRelevancy(),
        ],
        llm=llm,
        embeddings=embeddings,
    )

    # ── print report ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("RAGAS EVALUATION RESULTS")
    print("=" * 60)
    for metric, score in result.items():
        print(f"{metric:35s}: {score:.3f}")
    print("=" * 60)

    # ── save report ───────────────────────────────────────────
    report_path = ROOT / "eval" / "ragas_report.json"
    with open(report_path, "w") as f:
        json.dump(
            {k: float(v) for k, v in result.items()} |
            {"sample_size": len(samples)},
            f, indent=2
        )
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()