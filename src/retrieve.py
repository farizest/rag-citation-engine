"""
Retrieval pipeline for the Northwind Robotics wiki corpus.

Given a question, embeds it with the same model used in embed.py,
searches the ChromaDB vector store, and returns the top-k most
relevant chunks with their metadata.

Run directly to test retrieval from the command line:
    python src/retrieve.py "how many weeks of parental leave do we get?"

"""
import json
import sys 
from pathlib import Path
# pyrefly: ignore [missing-import]
import chromadb
# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer
# pyrefly: ignore [missing-import]
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).parent.parent
CHROMA_DIR = ROOT / "data" / "chroma_db"
TOP_K = 5
COLLECTION_NAME = "northwind_wiki"
EMBED_MODEL = "all-MiniLM-L6-v2"

def load_collection():
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_collection(name = COLLECTION_NAME)
    return collection

def retrieve(query:str, k:int = TOP_K)->list[dict]:
    model = SentenceTransformer(EMBED_MODEL)
    collection = load_collection()
    query_vector = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings = query_vector,
        n_results = k,
    )
    chunks=[]
    for i in range(len(results["ids"][0])):
        chunks.append({
            "chunk_id": results["ids"][0][i],
            "text":     results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        }

        )
    return chunks

def bm25_search(query: str, k: int = TOP_K) -> list[dict]:
    # ── load all chunks ───────────────────────────────────────
    chunks_path = ROOT / "data" / "processed" / "chunks.jsonl"
    all_chunks = []
    with open(chunks_path, "r") as f:
        for line in f:
            all_chunks.append(json.loads(line))

    # ── build BM25 index ──────────────────────────────────────
    tokenized_corpus = [
        chunk["text"].lower().split()
        for chunk in all_chunks
    ]
    bm25 = BM25Okapi(tokenized_corpus)

    # ── score query against index ─────────────────────────────
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # ── return top-k results ──────────────────────────────────
    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:k]

    results = []
    for idx in top_indices:
        results.append({
            "chunk_id": all_chunks[idx]["chunk_id"],
            "text":     all_chunks[idx]["text"],
            "metadata": {
                "source_file"    : all_chunks[idx]["source_file"],
                "department"     : all_chunks[idx]["department"],
                "page_title"     : all_chunks[idx]["page_title"],
                "section_heading": all_chunks[idx]["section_heading"],
                "token_count"    : all_chunks[idx]["token_count"],
            },
            "bm25_score": float(scores[idx]),
        })

    return results
def hybrid_search(query:str,k:int=TOP_K,fetch_k:int=10)->list[dict]:
    vector_results = retrieve(query,k=fetch_k)
    bm25_results = bm25_search(query,k=fetch_k)
    #build rank lookup tables
    vector_ranks = {
        r["chunk_id"]:rank for rank , r in enumerate(vector_results,start=1)
    }
    bm25_ranks = {
        r["chunk_id"]:rank for rank, r in enumerate(bm25_results,start=1)
    }
    all_chunk_ids = set(vector_ranks.keys()) | set(bm25_ranks.keys())
    RRF_K = 60
    rrf_scores = {}
    for chunk_id in all_chunk_ids:
        score = 0.0
        if chunk_id in vector_ranks:
            score += 1.0/(vector_ranks[chunk_id] + RRF_K)
        if chunk_id in bm25_ranks:
            score+= 1.0/(bm25_ranks[chunk_id]+RRF_K)
        rrf_scores[chunk_id] = score
    
    top_ids = sorted(
        rrf_scores,
        key= lambda cid:rrf_scores[cid],
        reverse=True
    )[:k]
    chunk_lookup = {
        
        r["chunk_id"]: r
        for r in vector_results + bm25_results
    }
    results = []
    for chunk_id in top_ids:
        chunk = chunk_lookup[chunk_id].copy()
        chunk["rrf_score"] = rrf_scores[chunk_id]
        results.append(chunk)

    return results

def main():
    if len(sys.argv) < 2:
        print('Usage: python src/retrieve.py "your question here"')
        return

    query = sys.argv[1]
    print(f"Query: {query}\n")

    results = retrieve(query)

    for rank, chunk in enumerate(results, start=1):
        meta = chunk["metadata"]
        print(f"#{rank}  distance={chunk['distance']:.3f}")
        print(f"   page : {meta['page_title']}")
        print(f"   file : {meta['source_file']}")
        print(f"   text : {chunk['text'][:120]}...")
        print()


if __name__ == "__main__":
    main()