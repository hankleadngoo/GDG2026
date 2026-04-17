# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Resume Protector** — a Multi-Agent LLM system for automated, transparent CV/resume evaluation built for GDGoC Hackathon Vietnam 2026 (Team AE107).

The system orchestrates 5 specialized AI agents in a pipeline to extract, verify via OSINT, cross-check, benchmark, and synthesize candidate assessments. Target domain: IT industry CVs/resumes/portfolios.

## Tech Stack

- **Backend:** Python + FastAPI
- **Frontend:** React or Next.js (scaffolded at `frontend/`)
- **Agent Framework:** LangGraph or CrewAI
- **LLMs:** Gemini 1.5 Pro (reasoning), Gemma (local, lightweight extraction)
- **Document Parsing:** LlamaParse or PyMuPDF
- **Embeddings:** Google Text Embedding API
- **Vector DB:** FAISS (local dev) → Vertex AI Vector Search (prod)
- **OSINT Tools:** Tavily Search API / Exa.ai, Proxycurl API / People Data Labs
- **Email:** Gmail API
- **Cloud:** Google Cloud Platform (Cloud Run, Cloud Storage, Firebase, Vertex AI)
- **Database:** PostgreSQL (Google Cloud SQL)
- **Containerization:** Docker + docker-compose

## Repository Structure

```
backend/
  main.py                          # FastAPI app entrypoint
  requirements.txt                 # Python dependencies
  api/
    routes.py                      # HTTP API endpoints
  workflow/
    graph.py                       # LangGraph/CrewAI pipeline orchestration
  agents/
    __init__.py
    agent1_extractor/parser.py     # Agent 1: CV parsing & link extraction
    agent2_osint/searcher.py       # Agent 2: OSINT web search (LinkedIn, GitHub, etc.)
    agent3_verifier/checker.py     # Agent 3: Cross-check CV claims vs OSINT data
    agent4_rag/retriever.py        # Agent 4: RAG over historical CVs for benchmarking
    agent5_synthesizer/reporter.py # Agent 5: Final assessment & hiring recommendation
frontend/
  package.json                     # Frontend dependencies (React/Next.js)
data/
  all-domains/                     # 1291 PDF CVs across all domains (RAG corpus)
  it-domain/                       # 649 IT-specific PDF CVs (focused benchmark corpus)
docs/
  GDG2026.md                       # Full project proposal (Vietnamese)
  architecture.png                 # System architecture diagram
docker-compose.yml                 # Multi-service local dev setup
.env.example                       # Environment variable template
```

## Architecture: 5-Agent Pipeline

The core workflow in `backend/workflow/graph.py` chains agents sequentially, with each agent capable of fallback planning if input data is insufficient:

1. **Agent 1 — Extractor** (`agent1_extractor/parser.py`): Parses CV PDF and extracts structured info + social/professional links (LinkedIn, GitHub, Facebook, etc.)

2. **Agent 2 — OSINT** (`agent2_osint/searcher.py`): Takes links from Agent 1, scrapes public profiles and filters relevant public information.

3. **Agent 3 — Verifier** (`agent3_verifier/checker.py`): Cross-references Agent 1 (CV claims) with Agent 2 (public data) to detect inconsistencies, missing info, or fraud. Returns a consolidated, verified candidate profile.

4. **Agent 4 — RAG Benchmarker** (`agent4_rag/retriever.py`): Retrieves relevant historical CVs from the vector database (`data/` corpus) for the target job role, establishing industry-average benchmarks.

5. **Agent 5 — Synthesizer** (`agent5_synthesizer/reporter.py`): Combines verified profile (Agent 3) + benchmark data (Agent 4) to produce a final assessment: skill comparison vs. industry average, job fit score, and hire/no-hire recommendation.

Each agent reports anomalies or gaps in its processing back to the recruiter in the final output. The system is designed with **Human-in-the-loop**: AI recommends, HR decides.

## Key Design Principles

- **Each agent has fallback logic**: If an agent cannot complete its task with available input, it produces a partial output with explicit caveats rather than blocking the pipeline.
- **Transparency over automation**: Every agent decision is explainable; gaps and inconsistencies are surfaced to the recruiter.
- **FAISS locally, Vertex AI in prod**: Vector search for RAG uses FAISS during development and Vertex AI Vector Search in production.
- **Self-learning loop**: After each recruitment cycle closes, hiring outcomes are fed back into the vector DB to improve future benchmarks (no manual retraining needed).

## Development Setup

All environment variables (API keys for Gemini, Tavily, Proxycurl, Gmail, GCP, etc.) go in `.env` based on `.env.example`.

Run locally with Docker:
```bash
docker-compose up
```

Backend only:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Data

- `data/all-domains/` — 1,291 PDF CVs spanning all industries (general RAG corpus)
- `data/it-domain/` — 649 IT-domain PDF CVs (used for IT-focused benchmarking during hackathon MVP)

These PDFs are the vector database source material. Indexing them with embeddings is a prerequisite before Agent 4 can function.
