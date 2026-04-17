# Tech Stack — Resume Protector

## At a Glance

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangGraph **or** CrewAI | Orchestrate multi-agent pipeline & state graph |
| LLM (primary) | Gemini 1.5 Pro | Complex reasoning, cross-referencing, report generation |
| LLM (lightweight) | Gemma (local) | Basic text extraction to save API tokens |
| Document Parsing | LlamaParse **or** PyMuPDF | Convert PDF/DOCX CVs to clean text |
| Embeddings | Google Text Embedding API | Vectorize CVs for semantic similarity search |
| OSINT – Web | Tavily Search API **or** Exa.ai | General web search for candidate info |
| OSINT – LinkedIn | Proxycurl API **or** People Data Labs | Structured LinkedIn profile extraction (JSON) |
| OSINT – GitHub | GitHub REST API | Repo list, commit history, language stats |
| Vector DB (dev) | FAISS | Local fast similarity search during development |
| Vector DB (prod) | Vertex AI Vector Search | Scalable cloud vector search in production |
| Candidate email | Gmail API | Auto-send clarification requests to candidates |
| Backend | Python + FastAPI | API server, agent orchestration entrypoint |
| Frontend | React **or** Next.js | HR recruiter dashboard |
| Relational DB | PostgreSQL (Google Cloud SQL) | Candidate records, interview state, audit log |
| Auth | Firebase Authentication | Recruiter login & session management |
| File Storage | Google Cloud Storage | CV/Portfolio PDF files |
| Containerization | Docker + docker-compose | Local development multi-service setup |
| Cloud Runtime | Google Cloud Run | Serverless autoscaling container deployment |
| MLOps | Vertex AI | Model deployment, monitoring, fine-tuning |
| Supplemental ML | PyTorch / scikit-learn | Optional classification/optimization tasks |

---

## Decision Points (Dev vs Prod)

```
                    Development              Production
Vector DB     →     FAISS (local)            Vertex AI Vector Search
LLM quota     →     Gemini free tier         Gemini paid / Vertex AI
Infrastructure→     docker-compose           Google Cloud Run
Storage       →     local filesystem         Google Cloud Storage
```

---

## AI Layer Detail

### LLM Routing
- **Gemma (local)**: Used in Agent 1 for raw text extraction — cheap, fast, no network latency, conserves Gemini quota.
- **Gemini 1.5 Pro**: Used in Agent 3 (cross-referencing reasoning) and Agent 5 (synthesis & report writing) where nuanced multi-step reasoning is required.

### Embedding Pipeline
1. CV text (from Agent 1) → Google Text Embedding API → vector
2. Stored in FAISS index (dev) / Vertex AI Vector Search (prod)
3. Agent 4 embeds the job description → nearest-neighbor search → retrieves top-K historical CVs

### Agent Framework Choice
- **LangGraph**: Preferred if the pipeline needs explicit conditional routing (e.g., branching on `osint_status`, looping on email resubmission). State is a typed graph node.
- **CrewAI**: Preferred for simpler sequential crew with built-in role definitions. Less boilerplate for straightforward pipelines.
- Both are free, open-source, Python-native. Decision should be made at project kickoff and committed to in `backend/workflow/graph.py`.

---

## External API Summary

| API | Used By | Key Concern |
|-----|---------|-------------|
| Gemini API | Agent 3, 5 | Rate limits on free tier; batch where possible |
| Tavily / Exa.ai | Agent 2 | Per-query cost; cache results per candidate session |
| Proxycurl / PDL | Agent 2 | Per-lookup cost; only call when LinkedIn URL present |
| GitHub REST API | Agent 2 | Unauthenticated: 60 req/hr; use PAT for higher limits |
| Gmail API | Agent 3 fallback | OAuth2 required; scoped to send-only |
| Google Text Embedding | Agent 1, 4 | Billed per character; batch embed historical CVs offline |

---

## Infrastructure (GCP)

```
Google Cloud Platform
├── Cloud Run            ← Backend (FastAPI) containers
├── Cloud SQL (PG)       ← Relational data
├── Cloud Storage        ← CV file storage
├── Vertex AI
│   ├── Vector Search    ← Production RAG index
│   └── Model Registry   ← Future: fine-tuned models
└── Firebase
    └── Authentication   ← Recruiter login
```

All services share a single GCP project. IAM service accounts are used for inter-service auth (no hardcoded credentials).
