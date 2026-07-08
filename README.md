# RAG Citation Engine

A production-grade "Ask My Docs" system built on a synthetic 90-page
company wiki. Demonstrates the full lifecycle of an enterprise RAG
pipeline: structure-aware document ingestion, hybrid retrieval (BM25 +
vector search), cross-encoder reranking, enforced citation grounding,
and a CI-gated evaluation pipeline.

Built without LangChain or LangGraph — every component is implemented
from scratch to demonstrate deep understanding of each layer.

---

## Why this project

Most RAG demos stop at "embed documents, query a vector store, generate
an answer." The gap between that and a production system is enormous.
This project closes that gap by implementing the patterns that enterprise
AI teams actually use:

- **Hybrid retrieval** — pure vector search fails on exact technical
  terms (config names, error codes, specific numbers). BM25 + vector
  search with Reciprocal Rank Fusion covers both semantic meaning and
  keyword precision.
- **Cross-encoder reranking** — embedding-based retrieval encodes query
  and document separately, losing nuance. A cross-encoder reads them
  together, dramatically improving precision on ambiguous queries.
- **Citation enforcement** — if the top reranked chunk scores below a
  confidence threshold, the system refuses to answer rather than
  hallucinating. Trustworthy silence beats confident fabrication.
- **CI-gated evaluation** — a 29-question golden eval set runs on every
  push. If retrieval quality drops below threshold, the build fails.

---

## Architecture

Question
│
▼
┌─────────────────────────────────────┐
│           Hybrid Retrieval          │
│  BM25 keyword search (rank-bm25)    │
│  +                                  │
│  Vector search (ChromaDB + MiniLM)  │
│  +                                  │
│  Reciprocal Rank Fusion (RRF)       │
└────────────────┬────────────────────┘
│ top 10 candidates
▼
┌─────────────────────────────────────┐
│         Cohere Reranking            │
│  cross-encoder scores query+chunk   │
│  together as a pair                 │
└────────────────┬────────────────────┘
│ top 5 reranked chunks
▼
┌─────────────────────────────────────┐
│       Citation Enforcement          │
│  top relevance score >= 0.25?       │
│  NO  → refuse to answer             │
│  YES → generate with Groq           │
└────────────────┬────────────────────┘
│
▼
Cited answer

---

## Before/After: why hybrid retrieval matters

Query: *"why did the fleet controller need to be sharded by warehouse?"*

| Approach | #1 Result | Correct? |
|---|---|---|
| Vector search only | Product Roadmap 2026 H1 | ❌ |
| Hybrid + Rerank | Postmortem: 2025 Fleet Controller Outage | ✅ |

Vector search missed because the answer's key term ("sharded") is a
rare, specific word that gets diluted in a dense embedding. BM25 finds
it immediately. RRF fusion combines both signals. The reranker confirms
the postmortem is the actual answer.

---

## Evaluation results

29-question golden eval set across four categories:

| Category | Questions | Retrieval hit rate | Faithfulness |
|---|---|---|---|
| Easy factual | 8 | 1.00 | 0.92 |
| Cross-reference | 8 | 0.88 | 0.85 |
| Technical exact | 6 | 0.86 | 0.86 |
| Out of scope | 7 | 1.00 | 1.00 |
| **Overall** | **29** | **0.93** | **0.90** |

Out-of-scope questions test citation enforcement — the system must
refuse rather than hallucinate. 7/7 correctly refused.

CI runs retrieval-only evaluation on every push (no LLM calls, no
quota issues). Full evaluation including faithfulness is run locally
before releases.

---

## Tech stack

| Component | Choice | Why |
|---|---|---|
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) | Local, free, no API quota |
| Vector store | ChromaDB (persistent, local) | Zero infra, file-based |
| Keyword search | `rank-bm25` (BM25Okapi) | Exact term matching |
| Reranking | Cohere Rerank API (`rerank-v3.5`) | Cross-encoder precision |
| Generation | Groq API (Llama 3.3 70B) | Fast, generous free tier |
| Evaluation | Custom script + golden set | Deterministic, CI-friendly |
| CI | GitHub Actions | Auto-runs eval on every push |

**No LangChain or LangGraph** — deliberate choice. Every component is
implemented from scratch so the decision-making at each layer
(chunking strategy, RRF fusion, confidence thresholding) is explicit,
auditable, and explainable.

---

## Project structure
rag-citation-engine/
├── data/
│   └── raw/                  synthetic wiki (90 markdown pages)
│       ├── engineering/      (30 pages: architecture, postmortems, runbooks)
│       ├── hr/               (20 pages: leave, compensation, onboarding)
│       ├── it_ops/           (15 pages: VPN, access, device policy)
│       ├── product/          (15 pages: roadmap, specs, release notes)
│       └── company/          (10 pages: mission, expenses, travel)
├── src/
│   ├── chunker.py            structure-aware markdown chunker
│   ├── embed.py              embedding + ChromaDB ingestion
│   ├── retrieve.py           vector search + BM25 + hybrid RRF
│   ├── rerank.py             Cohere cross-encoder reranking
│   └── generate.py           citation-enforced answer generation
├── tests/
│   └── test_retrieve.py      retrieval unit tests
├── eval/
│   ├── golden_set.jsonl      29 manually verified Q&A pairs
│   └── evaluate.py           retrieval + faithfulness scoring
└── .github/
└── workflows/
└── eval.yml          CI: runs eval on every push

---

## Setup

### Prerequisites
- Python 3.10+
- [Groq API key](https://console.groq.com) (free)
- [Cohere API key](https://dashboard.cohere.com) (free, 1000 calls/month)

### Install

```bash
git clone https://github.com/farizest/rag-citation-engine.git
cd rag-citation-engine
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Build the pipeline

```bash
# 1. Chunk the wiki corpus
python src/chunker.py

# 2. Embed chunks and build vector store
python src/embed.py

# 3. Ask a question
python src/generate.py "how many weeks of parental leave do we get?"
```

---

## Usage examples

**Easy factual question:**

Question: how many weeks of parental leave do we get?
Answer: Northwind Robotics provides 16 weeks of fully paid parental
leave for the primary caregiver and 8 weeks for a secondary caregiver
[Source: Parental Leave Policy].

**Hard cross-reference question:**
Question: why did the fleet controller need to be sharded by warehouse?
Answer: The Fleet Controller needed to be sharded by warehouse because
a single instance handling multiple warehouses experienced severe task
assignment latency degradation during peak shift changes, peaking at
14.2 seconds p99 against a 500ms SLO [Source: Postmortem: 2025 Fleet
Controller Outage]. The root cause was an O(n²) conflict-resolution
algorithm that scaled poorly with concurrent pending tasks across
multiple warehouses [Source: Fleet Controller Service].

**Out-of-scope question (citation enforcement):**
Question: what is the company stock ticker symbol?
Answer: I don't have enough information in the Northwind wiki to
answer this question confidently. Please check with your manager
or the relevant team directly.

---

## Running the evaluation

```bash
# Full evaluation (retrieval + faithfulness, uses Groq API)
python eval/evaluate.py

# Retrieval-only (no LLM calls, used in CI)
RETRIEVAL_ONLY=true python eval/evaluate.py
```

---

## Known limitations and future work

- **Synthetic corpus** — real-world documents add noise, inconsistency,
  and mixed formats that would stress-test the chunking strategy further
- **Model reload latency** — `SentenceTransformer` reloads on every
  query; production fix is module-level caching
- **BM25 rebuilt per query** — precomputing and caching the index at
  startup would reduce latency significantly
- **No conversation memory** — every question is stateless; multi-turn
  conversation would require session management
- **String-matching faithfulness** — evaluates whether expected phrases
  appear in the answer; LLM-as-judge would be more semantically accurate

---

## Deliberate design decisions

**Why no LangChain?** LangChain would have abstracted away the chunking
strategy, RRF fusion logic, and confidence thresholding — exactly the
parts that demonstrate engineering judgment. Raw Python makes every
decision explicit and auditable.

**Why local embeddings?** Cloud embedding APIs (Voyage AI, OpenAI) add
rate limits and billing friction to a development loop. `all-MiniLM-L6-v2`
runs locally, starts instantly, and produces quality vectors sufficient
for a 90-page corpus.

**Why RRF over score normalization?** BM25 scores and cosine distances
are in completely different units. RRF fuses ranked lists using only
position, not magnitude — no normalization required, no hyperparameter
tuning per query.

**Why Groq over OpenAI?** Generous free tier (no credit card), faster
inference, and OpenAI-compatible API means zero vendor lock-in.
