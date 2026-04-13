# Project Structure — Resume Protector

## Repository Layout

```
GDG2026/
│
├── backend/                          # Python FastAPI server + all AI logic
│   ├── main.py                       # App entrypoint: FastAPI init, router mount, startup hooks
│   ├── requirements.txt              # Python dependencies
│   │
│   ├── api/
│   │   └── routes.py                 # HTTP endpoints (POST /evaluate, GET /report/{id}, ...)
│   │
│   ├── workflow/
│   │   └── graph.py                  # LangGraph / CrewAI pipeline definition
│   │                                 # Wires agents together, defines state schema,
│   │                                 # handles conditional edges (OSINT branch, email branch)
│   │
│   └── agents/
│       ├── __init__.py
│       ├── agent1_extractor/
│       │   └── parser.py             # CV parsing → structured profile + links
│       ├── agent2_osint/
│       │   └── searcher.py           # OSINT: web search + LinkedIn + GitHub
│       ├── agent3_verifier/
│       │   └── checker.py            # Cross-reference CV vs OSINT; trust scoring
│       ├── agent4_rag/
│       │   └── retriever.py          # Vector search over historical CVs; benchmark stats
│       └── agent5_synthesizer/
│           └── reporter.py           # Final report generation; hire recommendation
│
├── frontend/                         # React / Next.js HR dashboard
│   └── package.json                  # JS dependencies (framework TBD)
│
├── data/
│   ├── all-domains/                  # 1 291 PDF CVs — general benchmark corpus
│   │                                 # (all industries, used for broad RAG base)
│   └── it-domain/                    # 649 PDF CVs — IT-specific benchmark corpus
│                                     # (primary benchmark source for MVP)
│
├── docs/
│   ├── GDG2026.md                    # Full project proposal (Vietnamese)
│   └── architecture.png             # System architecture diagram
│
├── plans/                            # This planning directory
│   ├── dataflow.md                   # Agent-by-agent data flow
│   ├── techstack.md                  # Technology decisions & rationale
│   ├── business.md                   # Problem, solution, users, roadmap
│   ├── structure.md                  # This file
│   └── tasks.md                      # Implementation task list
│
├── docker-compose.yml                # Local multi-service orchestration
├── .env.example                      # Required environment variables template
├── CLAUDE.md                         # AI assistant guidance for this repo
└── README.md                         # Project overview (to be filled)
```

---

## Backend Module Responsibilities

### `backend/main.py`
- Initializes the FastAPI application.
- Mounts the `api/routes.py` router.
- On startup: loads FAISS index (or connects to Vertex AI), warms up embedding model.

### `backend/api/routes.py`
Key endpoints to implement:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/evaluate` | Accept CV file upload + job description; trigger agent pipeline |
| `GET` | `/report/{job_id}` | Return assessment report for a completed pipeline run |
| `GET` | `/status/{job_id}` | Poll pipeline execution status |
| `POST` | `/feedback/{job_id}` | HR submits hire/reject decision (triggers self-learning) |

### `backend/workflow/graph.py`
- Defines the `AgentState` TypedDict shared across all agents.
- Builds the LangGraph `StateGraph` (or CrewAI `Crew`) wiring:
  - Node: `extract` → `osint` (conditional on links) → `verify` → `benchmark` → `synthesize`
  - Conditional edge after `verify`: if `trust_score < threshold` → `send_email` node
- Handles async execution; each agent node is an `async def`.

### `backend/agents/agent1_extractor/parser.py`
- Input: raw bytes (PDF/DOCX)
- Uses LlamaParse or PyMuPDF to extract text
- Uses Gemma (local) to structure text into `candidate_profile` dict
- Extracts all URLs and classifies them by platform

### `backend/agents/agent2_osint/searcher.py`
- Input: `extracted_links` + `candidate_profile` (for name-based fallback search)
- Calls Tavily/Exa for web search, Proxycurl for LinkedIn, GitHub API for repos
- Returns raw structured data per platform; does not judge — just collects

### `backend/agents/agent3_verifier/checker.py`
- Input: `candidate_profile` (from A1) + `osint_data` (from A2)
- Uses Gemini 1.5 Pro to reason about discrepancies
- Produces `verified_profile`, `contradictions[]`, `trust_score`
- If `trust_score < 0.5`: sets `email_sent = True`, triggers Gmail API

### `backend/agents/agent4_rag/retriever.py`
- Input: job role / job description text
- Embeds JD with Google Text Embedding API
- Queries FAISS / Vertex AI for top-K similar CVs
- Aggregates skill frequencies, experience distributions → `benchmark` dict

### `backend/agents/agent5_synthesizer/reporter.py`
- Input: `verified_profile` + `benchmark`
- Uses Gemini 1.5 Pro with a structured prompt to produce `final_report`
- Includes: skill gap, percentile score, job-fit score, hire recommendation, caveats

---

## Frontend Structure (To Be Designed)

The frontend is an HR recruiter dashboard. Minimum screens needed:

1. **Upload screen** — CV file upload + job description input field
2. **Pipeline status** — real-time progress indicator per agent step
3. **Report view** — final assessment display with skill breakdown, trust score, recommendation
4. **Decision screen** — HR approve / reject button (submits feedback to `/feedback/{job_id}`)
5. **History** — list of past evaluations with outcomes

---

## Configuration & Secrets

All secrets go in `.env` (copied from `.env.example`). Expected keys:

```
# LLM
GOOGLE_API_KEY=               # Gemini + Text Embedding API

# OSINT
TAVILY_API_KEY=
PROXYCURL_API_KEY=
GITHUB_PAT=                   # Optional: raises GitHub API rate limit

# Email
GMAIL_OAUTH_CLIENT_ID=
GMAIL_OAUTH_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=

# GCP
GCP_PROJECT_ID=
GCP_REGION=
VERTEX_AI_INDEX_ID=           # Prod only

# Database
DATABASE_URL=                 # PostgreSQL connection string

# Firebase
FIREBASE_SERVICE_ACCOUNT_JSON=
```

---

## Data Corpus Structure

```
data/all-domains/     ← 1 291 PDFs, mixed industries
data/it-domain/       ← 649 PDFs, IT-specific

Indexing pipeline (run once, offline):
  PDF files → Agent 1 parser (batch) → embeddings → FAISS index saved to disk
  On prod: upload index to Vertex AI Vector Search
```

The FAISS index file should be committed to `.gitignore` (binary, large). Provide a `scripts/build_index.py` to rebuild it from the PDF corpus.
