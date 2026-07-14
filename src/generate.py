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
from google import genai

# pyrefly: ignore [missing-import]
from openai import OpenAI
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from retrieve import hybrid_search
from rerank import rerank

load_dotenv()

GEMINI_MODEL           = "gemini-2.5-flash"
CONFIDENCE_THRESHOLD = 0.25

SYSTEM_PROMPT = """You are a helpful document assistant that answers \
questions using ONLY the provided document excerpts.

Rules:
1. Answer using ONLY information found in the provided context. Do \
not use any outside knowledge, even if you think you know the answer.
2. Every claim in your answer must be followed by a citation in the \
format [Source: <page title>].
3. If the context does not contain enough information to answer the \
question, say so explicitly. Never guess or fabricate an answer.
4. Be concise, clear, and direct. Do not repeat the question back.
5. If multiple sources support the answer, cite all of them."""


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
    return f"""Document excerpts:

{context}

---

Question: {question}

Answer using only the excerpts above. Cite every claim."""


def check_confidence(chunks: list[dict]) -> bool:
    if not chunks:
        return False
    top_score = chunks[0].get("relevance_score", 0.0)
    return top_score >= CONFIDENCE_THRESHOLD


def generate_answer(question: str, chunks: list[dict]) -> str:
    if not check_confidence(chunks):
        return (
            "I don't have enough information in the uploaded documents "
            "to answer this question confidently. Please upload a relevant "
            "document or rephrase your question."
        )
    client = genai.Client(
    api_key=os.environ["GOOGLE_API_KEY"]
)

    context = format_context(chunks)
    prompt  = build_prompt(question, context)

    response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
        )

    return response.text


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