"""
Request and response models for the RAG Citation Engine API.
Pydantic models give us automatic validation and clear API contracts.
"""
from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    message: str
    chunks_added: int
    total_chunks: int


class ChatRequest(BaseModel):
    question: str


class Source(BaseModel):
    page_title: str
    source_file: str
    relevance_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    confidence: str


class ResetResponse(BaseModel):
    message: str