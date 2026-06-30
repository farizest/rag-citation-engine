"""
Embedding pipeline for the Northwind Robotics wiki corpus.

Reads chunks from data/processed/chunks.jsonl, embeds them using
a local sentence-transformers model (no API key required), and stores
vectors + metadata in a local ChromaDB collection.

Run this once after chunker.py to populate the vector store:
    python src/embed.py
"""
import json
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

ROOT            = Path(__file__).parent.parent
CHUNKS_FILE     = ROOT / "data" / "processed" / "chunks.jsonl"
CHROMA_DIR      = ROOT / "data" / "chroma_db"

COLLECTION_NAME = "northwind_wiki"
EMBED_MODEL     = "all-MiniLM-L6-v2"
BATCH_SIZE      = 32


def load_chunks(path: Path) -> list[dict]:
    chunks = []
    with open(path, "r") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def embed_and_store(chunks: list[dict]) -> None:
    # ── set up clients ────────────────────────────────────────
    print(f"Loading embedding model '{EMBED_MODEL}'...")
    model = SentenceTransformer(EMBED_MODEL)

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # ── idempotency check ─────────────────────────────────────
    if collection.count() > 0:
        print(f"Collection '{COLLECTION_NAME}' already has "
              f"{collection.count()} vectors. Skipping embedding.")
        print("Delete data/chroma_db/ to force a re-embed.")
        return

    # ── embed in batches ──────────────────────────────────────
    print(f"Embedding {len(chunks)} chunks in batches of {BATCH_SIZE}...")
    all_ids        = []
    all_embeddings = []
    all_documents  = []
    all_metadatas  = []

    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start : batch_start + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        vectors = model.encode(
            texts,
            show_progress_bar=False,
        ).tolist()

        for chunk, vector in zip(batch, vectors):
            all_ids.append(chunk["chunk_id"])
            all_embeddings.append(vector)
            all_documents.append(chunk["text"])
            all_metadatas.append({
                "source_file"    : chunk["source_file"],
                "department"     : chunk["department"],
                "page_title"     : chunk["page_title"],
                "section_heading": chunk["section_heading"],
                "token_count"    : chunk["token_count"],
            })

        print(f"  embedded batch {batch_start // BATCH_SIZE + 1}"
              f" / {-(-len(chunks) // BATCH_SIZE)}")

    # ── store in chromadb ─────────────────────────────────────
    collection.add(
        ids        = all_ids,
        embeddings = all_embeddings,
        documents  = all_documents,
        metadatas  = all_metadatas,
    )
    print(f"Stored {collection.count()} vectors in '{COLLECTION_NAME}'")


def main():
    print("Loading chunks...")
    chunks = load_chunks(CHUNKS_FILE)
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE.name}")

    embed_and_store(chunks)
    print("Done. Vector store is ready at data/chroma_db/")


if __name__ == "__main__":
    main()