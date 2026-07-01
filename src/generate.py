"""
Generation pipeline for the Northwind Robotics wiki corpus.

Takes a user question, retrieves relevant chunks, and asks Gemini to
answer using ONLY that retrieved context -- with citations back to the
source file for every claim.

Run directly to test end-to-end retrieval + generation:
    python src/generate.py "how many weeks of parental leave do we get?"
"""
import os
import sys
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from retrieve import retrieve

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"

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


def generate_answer(question: str, chunks: list[dict]) -> str:
    client = genai.Client(
        api_key=os.environ["GOOGLE_API_KEY"]
    )

    context = format_context(chunks)
    prompt = build_prompt(question, context)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=1024,
        ),
    )

    return response.text


def main():
    if len(sys.argv) < 2:
        print('Usage: python src/generate.py "your question here"')
        return

    question = sys.argv[1]
    print(f"Question: {question}\n")

    print("Retrieving relevant chunks...")
    chunks = retrieve(question, k=5)

    print(f"Retrieved {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"  - {chunk['metadata']['page_title']} "
              f"(distance={chunk['distance']:.3f})")

    print("\nGenerating answer...\n")
    answer = generate_answer(question, chunks)

    print("=" * 60)
    print(answer)
    print("=" * 60)


if __name__ == "__main__":
    main()