# RAG Citation Engine

A production-grade, domain-specific "ask my docs" system built on a
synthetic company wiki (90 pages across engineering, HR, IT, product,
and company-wide documentation). Combines hybrid retrieval (BM25 +
vector search), cross-encoder reranking, and enforced citation grounding
-- the system refuses to answer if it can't back a claim with retrieved
text. Includes a CI-gated evaluation pipeline so retrieval quality
regressions fail the build automatically.

## Why this project

[To be filled in: the gap between a RAG demo and a production RAG
system, and why this project demonstrates the difference.]

## Architecture

[To be filled in once Phase 1 is complete: diagram + explanation of the
ingestion -> retrieval -> generation pipeline.]

## Status

- [x] Phase 1: Corpus, chunking
- [ ] Phase 1: Embedding, vector store, basic retrieval + generation
- [ ] Phase 2: Hybrid retrieval, reranking, citation enforcement
- [ ] Phase 3: Golden eval set, CI-gated evaluation

## Setup

```bash
git clone https://github.com/<your-username>/rag-citation-engine.git
cd rag-citation-engine
pip install -r requirements.txt
cp .env.example .env  # then fill in your API keys
```

## Project structure

```
data/raw/        synthetic company wiki source (90 markdown pages)
data/processed/  generated chunks (gitignored, regenerate via src/chunker.py)
src/             pipeline code: chunking, embedding, retrieval, generation
tests/           unit tests
eval/            golden eval set + evaluation harness (Phase 3)
```