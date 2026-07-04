"""
Reranking pipeline for the Northwind Robotics wiki corpus.

Takes hybrid search candidates and reranks them using Cohere's
cross-encoder rerank API, which scores each chunk by reading the
query and chunk together as a pair -- much more precise than
embedding similarity alone.

Usage (called from generate.py, not directly):
    from rerank import rerank
"""
import os
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
import cohere

load_dotenv()

COHERE_MODEL = "rerank-v3.5"
TOP_N        = 5

def rerank(query: str, chunks: list[dict], top_n: int = TOP_N) -> list[dict]:
    client = cohere.ClientV2(
        api_key=os.environ["COHERE_API_KEY"]
    )

    # ── extract texts for cohere ──────────────────────────────
    documents = [chunk["text"] for chunk in chunks]

    # ── call cohere rerank ────────────────────────────────────
    response = client.rerank(
        model=COHERE_MODEL,
        query=query,
        documents=documents,
        top_n=top_n,
    )

    # ── rebuild result list in reranked order ─────────────────
    reranked = []
    for result in response.results:
        chunk = chunks[result.index].copy()
        chunk["relevance_score"] = result.relevance_score
        reranked.append(chunk)

    return reranked
def main():
    import sys
    sys.path.insert(0, "src")
    from retrieve import hybrid_search

    if len(sys.argv) < 2:
        print('Usage: python src/rerank.py "your question here"')
        return

    query = sys.argv[1]
    print(f"Query: {query}\n")

    print("Running hybrid search...")
    candidates = hybrid_search(query, k=10)
    print(f"Got {len(candidates)} candidates\n")

    print("Reranking...")
    results = rerank(query, candidates, top_n=5)

    print("=== RERANKED RESULTS ===")
    for i, chunk in enumerate(results, 1):
        print(f"#{i}  relevance={chunk['relevance_score']:.4f}"
              f" | {chunk['metadata']['page_title']}")


if __name__ == "__main__":
    main()