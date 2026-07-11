"""
FastAPI backend for the RAG Citation Engine.

Endpoints:
    POST /upload   — upload a document, chunk and embed it
    POST /chat     — ask a question, get a cited answer
    DELETE /reset  — clear all uploaded documents
    GET  /status   — how many chunks are in the collection
"""
import os
import sys
import uuid
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

# pyrefly: ignore [missing-import]
from chunker import chunk_file
# pyrefly: ignore [missing-import]
from rerank import rerank
# pyrefly: ignore [missing-import]
from generate import generate_answer, check_confidence
from models import (
    UploadResponse, ChatRequest, ChatResponse,
    Source, ResetResponse
)

load_dotenv()

app = FastAPI(title="RAG Citation Engine", version="1.0.0")

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static"
)
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR      = ROOT / "data" / "user_chroma_db"
COLLECTION_NAME = "user_documents"
EMBED_MODEL     = "all-MiniLM-L6-v2"

# ── load once at startup, reuse across all requests ──────────
_model      = SentenceTransformer(EMBED_MODEL)
_chroma     = chromadb.PersistentClient(path=str(CHROMA_DIR))

def get_collection():
    return _chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


@app.get("/")
async def root():
    html_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/status")
async def status():
    collection = get_collection()
    return {
        "total_chunks": collection.count(),
        "ready": collection.count() > 0,
    }


@app.delete("/reset")
async def reset():
    try:
        _chroma.delete_collection(COLLECTION_NAME)
        get_collection()
        return ResetResponse(message="Collection cleared. Ready for new documents.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    # ── validate file type ────────────────────────────────────
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. "
                   f"Supported: {SUPPORTED_EXTENSIONS}"
        )

    # ── save to temp file so chunk_file() can read it ─────────
    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
                # ── chunk the document ────────────────────────────────
        # Pass the original user-uploaded filename (without extension) as the override title
        chunks = chunk_file(tmp_path, override_title=Path(file.filename).stem)


        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="Document produced no chunks. "
                       "Check that the file has readable text content."
            )

        # ── embed and store ───────────────────────────────────
        collection = get_collection()
        texts      = [c.text for c in chunks]
        vectors    = _model.encode(
            texts,
            show_progress_bar=False,
        ).tolist()

        ids = [
            f"{file.filename}::{c.section_heading}::{i}"
            for i, c in enumerate(chunks)
        ]

        metadatas = [
            {
                "source_file"    : file.filename,
                "page_title"     : c.page_title or file.filename,
                "section_heading": c.section_heading,
                "token_count"    : c.token_count,
                "department"     : "uploaded",
            }
            for c in chunks
        ]

        collection.add(
            ids        = ids,
            embeddings = vectors,
            documents  = texts,
            metadatas  = metadatas,
        )

        return UploadResponse(
            message      = f"'{file.filename}' processed successfully.",
            chunks_added = len(chunks),
            total_chunks = collection.count(),
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        tmp_path.unlink(missing_ok=True)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    collection = get_collection()

    # ── guard: no documents uploaded yet ─────────────────────
    if collection.count() == 0:
        return ChatResponse(
            answer="No documents uploaded yet. Please upload a document first.",
            sources=[],
            confidence="none",
        )

    # ── vector search directly on user collection ─────────────
    query_vector = _model.encode([request.question]).tolist()
    results = collection.query(
        query_embeddings=query_vector,
        n_results=min(10, collection.count()),
    )

    # ── build candidate chunks for reranker ───────────────────
    candidates = []
    for i in range(len(results["ids"][0])):
        candidates.append({
            "chunk_id": results["ids"][0][i],
            "text"    : results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    # ── rerank candidates ─────────────────────────────────────
    reranked = rerank(request.question, candidates, top_n=5)

    # ── generate cited answer ─────────────────────────────────
    answer = generate_answer(request.question, reranked)

    # ── determine confidence label ────────────────────────────
    top_score = reranked[0].get("relevance_score", 0.0)
    if top_score >= 0.7:
        confidence = "high"
    elif top_score >= 0.25:
        confidence = "medium"
    else:
        confidence = "low"

    # ── build sources list ────────────────────────────────────
    sources = [
        Source(
            page_title     = c["metadata"]["page_title"],
            source_file    = c["metadata"]["source_file"],
            relevance_score= round(c["relevance_score"], 3),
        )
        for c in reranked
        if c["relevance_score"] >= 0.25
    ]

    return ChatResponse(
        answer    = answer,
        sources   = sources,
        confidence= confidence,
    )
@app.on_event("startup")
async def startup_event():
    print("RAG Citation Engine starting...")
    print(f"Vector store: {CHROMA_DIR}")
    collection = get_collection()
    print(f"Documents in collection: {collection.count()}")
    print("Ready.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=7860,
        reload=False,
    )