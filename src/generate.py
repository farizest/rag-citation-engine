"""
Generation pipeline for the Northwind Robotics wiki corpus.

Takes a user question, retrieves relevant chunks via hybrid search,
reranks them with Cohere, and asks Groq (Llama 3.3 70B) to answer
using ONLY that retrieved context -- with citations back to the
source file for every claim.

Run directly to test end-to-end retrieval + generation:
    python src/generate.py "how many weeks of parental leave do we get?"
"""
import os
import sys
from pathlib import Path

# pyrefly: ignore [missing-import]
from openai import OpenAI
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from retrieve import hybrid_search
from rerank import rerank

load_dotenv()

GROQ_MODEL           = "llama-3.3-70b-versatile"
CONFIDENCE_THRESHOLD = 0.25

SYSTEM_PROMPT = """You are an internal assistant for Northwind Robotics \
employees, answering questions using ONLY the wiki excerpts provided below.

Rules:
1. Answer using ONLY information found in the provided context. Do not \
use any outside knowledge, even if you think you know the answer.
2. Every claim in your answer must be followed by a citation in the \
format [Source: <page title>].
3. If the provided context does not contain enough information to \
answer the question, say so explicitly. Do not guess or make up an \
answer.
4. Be concise and direct. Do not repeat the question back."""


def format_context(chunks: list[dict]) -> str:
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk["metadata"]
        block = (
            f"[Excerpt {i}] Source: {meta['page_title']} "
            f"({meta['source_file']})\n"
            f"{chunk['text']}"
        )
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)


def build_prompt(question: str, context: str) -> str:
    return f"""Context (wiki excerpts):

{context}

---

Question: {question}

Answer the question using only the context above, following the rules \
in your instructions."""


def check_confidence(chunks: list[dict]) -> bool:
    if not chunks:
        return False
    top_score = chunks[0].get("relevance_score", 0.0)
    return top_score >= CONFIDENCE_THRESHOLD


def generate_answer(question: str, chunks: list[dict]) -> str:
    if not check_confidence(chunks):
        return (
            "I don't have enough information in the Northwind wiki "
            "to answer this question confidently. Please check with "
            "your manager or the relevant team directly."
        )

    client = OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )

    context = format_context(chunks)
    prompt  = build_prompt(question, context)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=1024,
    )

    return response.choices[0].message.content


def main():
    if len(sys.argv) < 2:
        print('Usage: python src/generate.py "your question here"')
        return

    question = sys.argv[1]
    print(f"Question: {question}\n")

    print("Running hybrid search...")
    candidates = hybrid_search(question, k=10)

    print("Reranking candidates...")
    chunks = rerank(question, candidates, top_n=5)

    print(f"Top chunk relevance: {chunks[0]['relevance_score']:.4f}\n")

    print("Retrieved chunks:")
    for chunk in chunks:
        print(f"  - {chunk['metadata']['page_title']} "
              f"(relevance={chunk['relevance_score']:.4f})")

    print("\nGenerating answer...\n")
    answer = generate_answer(question, chunks)

    print("=" * 60)
    print(answer)
    print("=" * 60)


if __name__ == "__main__":
    main()