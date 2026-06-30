"""
Retrieval pipeline for the Northwind Robotics wiki corpus.

Given a question, embeds it with the same model used in embed.py,
searches the ChromaDB vector store, and returns the top-k most
relevant chunks with their metadata.

Run directly to test retrieval from the command line:
    python src/retrieve.py "how many weeks of parental leave do we get?"

"""

import sys 
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

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