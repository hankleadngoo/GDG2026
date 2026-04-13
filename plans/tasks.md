# Implementation Tasks — Resume Protector (Hackathon MVP)

Tasks are ordered by dependency. Work items within the same phase can be parallelized across team members.

---

## Phase 0 — Foundation (Day 1 Morning)

- [ ] **0.1** Decide and commit to agent framework: **LangGraph** vs CrewAI  
  _Recommendation: LangGraph — needed for conditional routing (OSINT branch, email branch)_

- [ ] **0.2** Decide and commit to document parser: **LlamaParse** vs PyMuPDF  
  _Recommendation: PyMuPDF for zero-cost offline parsing; LlamaParse if complex layouts needed_

- [ ] **0.3** Set up `.env` with all required API keys (see `plans/structure.md` for key list)

- [ ] **0.4** Verify all external API access works:  
  - Gemini API (Google AI Studio)  
  - Tavily or Exa.ai  
  - Proxycurl or People Data Labs  
  - GitHub REST API (with PAT)  
  - Gmail API (OAuth2 flow completed)

- [ ] **0.5** `docker-compose.yml` — define services: `backend`, `frontend`, `postgres`

- [ ] **0.6** `backend/requirements.txt` — pin all Python dependencies:  
  `fastapi`, `uvicorn`, `langgraph` or `crewai`, `pymupdf` or `llama-parse`,  
  `google-generativeai`, `faiss-cpu`, `langchain-google-genai`,  
  `tavily-python`, `PyGithub`, `google-auth`, `psycopg2-binary`, etc.

---

## Phase 1 — Agent 1: CV Extractor (Day 1)

- [ ] **1.1** `agent1_extractor/parser.py` — implement PDF/DOCX text extraction using PyMuPDF  
  Output: raw text string

- [ ] **1.2** Design `candidate_profile` schema (Python dataclass or TypedDict):  
  `name`, `email`, `phone`, `skills[]`, `experience[]`, `education[]`, `links[]`

- [ ] **1.3** Implement Gemma local inference call to structure raw text → `candidate_profile`  
  Use `ollama` or `transformers` pipeline for local Gemma

- [ ] **1.4** Implement URL extraction + platform classification (LinkedIn / GitHub / Facebook / other)

- [ ] **1.5** Unit test: parse 5 sample IT CVs from `it-domain/`; verify output schema is correct

---

## Phase 2 — Agent 4: RAG Indexer & Retriever (Day 1, parallel with Phase 1)

- [ ] **2.1** `scripts/build_index.py` — batch process all PDFs in `data/it-domain/` through Agent 1 parser  
  → embed each `candidate_profile` using Google Text Embedding API  
  → build and save FAISS index to `data/faiss_it.index`

- [ ] **2.2** `agent4_rag/retriever.py` — implement job description embedding + FAISS nearest-neighbor search  
  → retrieve top-K (default K=20) similar profiles  
  → aggregate: skill frequency, avg years of experience, score distribution

- [ ] **2.3** Test: query "Senior Python Backend Engineer" → inspect retrieved profiles for relevance

---

## Phase 3 — Agent 2: OSINT Searcher (Day 1–2)

- [ ] **3.1** `agent2_osint/searcher.py` — implement LinkedIn fetch via Proxycurl / PDL  
  Input: LinkedIn URL → Output: structured JSON (headline, skills, positions)

- [ ] **3.2** Implement GitHub fetch via GitHub REST API  
  Input: GitHub username or URL → Output: repo list, top languages, recent commit count

- [ ] **3.3** Implement general web search via Tavily / Exa.ai  
  Input: candidate name + role → Output: top-5 relevant search snippets

- [ ] **3.4** Implement graceful degradation: if any source fails or is private → `osint_status = "partial"`, log which sources were skipped

- [ ] **3.5** Test: run Agent 2 on 3 real-world LinkedIn + GitHub profiles; verify data extraction

---

## Phase 4 — Agent 3: Verifier (Day 2)

- [ ] **4.1** `agent3_verifier/checker.py` — design Gemini 1.5 Pro prompt for cross-referencing:  
  Input: `candidate_profile` (CV) + `osint_data` (public)  
  Task: identify contradictions, missing claims, unverifiable statements

- [ ] **4.2** Implement structured output parsing: `contradictions[]`, `trust_score` (0.0–1.0)

- [ ] **4.3** Implement Gmail API integration:  
  - If `trust_score < 0.5` → compose and send clarification email to candidate  
  - Email template: list specific contradictions found; request supporting evidence

- [ ] **4.4** Test: create synthetic CV with 3 deliberate contradictions → verify Agent 3 catches them

---

## Phase 5 — Agent 5: Synthesizer (Day 2)

- [ ] **5.1** `agent5_synthesizer/reporter.py` — design Gemini 1.5 Pro prompt for final synthesis:  
  Input: `verified_profile` + `benchmark`  
  Output: structured report JSON

- [ ] **5.2** Define `final_report` schema:  
  `skill_gap[]`, `percentile_score`, `job_fit_score` (0–100), `hire_recommendation` (bool),  
  `strengths[]`, `concerns[]`, `pipeline_warnings[]`

- [ ] **5.3** Test: run full pipeline on 3 sample IT CVs end-to-end; review report quality

---

## Phase 6 — Pipeline Wiring (Day 2)

- [ ] **6.1** `backend/workflow/graph.py` — define `AgentState` TypedDict with all fields

- [ ] **6.2** Build LangGraph `StateGraph`:  
  Nodes: `extract` → `osint` → `verify` → `benchmark` → `synthesize`  
  Conditional edge after `verify`: if low trust → `send_email` node before `synthesize`

- [ ] **6.3** Implement async execution; ensure agents 3 and 4 can run in parallel (both feed into 5)

- [ ] **6.4** Integration test: upload a real IT CV PDF → pipeline runs end-to-end → report produced

---

## Phase 7 — API & Backend (Day 2–3)

- [ ] **7.1** `backend/api/routes.py` — implement `POST /evaluate`:  
  Accept multipart form (CV file + job description text)  
  Trigger pipeline as background task; return `job_id`

- [ ] **7.2** Implement `GET /status/{job_id}` — return current pipeline step

- [ ] **7.3** Implement `GET /report/{job_id}` — return completed `final_report`

- [ ] **7.4** Implement `POST /feedback/{job_id}` — accept HR decision; store in PostgreSQL for feedback loop

- [ ] **7.5** `backend/main.py` — wire up FastAPI app, mount router, startup FAISS index load

---

## Phase 8 — Frontend Dashboard (Day 2–3, parallel)

- [ ] **8.1** Scaffold React / Next.js app in `frontend/`

- [ ] **8.2** **Upload screen**: file picker (PDF/DOCX) + job description textarea + submit button

- [ ] **8.3** **Status screen**: poll `/status/{job_id}` every 2s; show step-by-step progress bar (5 agents)

- [ ] **8.4** **Report screen**: display `final_report` — skill gap table, trust score badge, hire/no-hire banner, warnings list

- [ ] **8.5** **Decision screen**: Approve / Reject buttons → call `POST /feedback/{job_id}`

- [ ] **8.6** Basic responsive layout; no external design system required for MVP

---

## Phase 9 — Integration & Demo Prep (Day 3)

- [ ] **9.1** End-to-end smoke test: 5 diverse IT CVs through the full system

- [ ] **9.2** Verify all `pipeline_warnings` surface correctly when OSINT is partial or skipped

- [ ] **9.3** Prepare 3 demo scenarios:
  - Scenario A: Strong candidate, OSINT confirms CV, high trust score → recommend hire
  - Scenario B: Candidate with inflated claims caught by OSINT → contradiction flagged, email sent
  - Scenario C: No social links → CV-only evaluation with appropriate caveats

- [ ] **9.4** `docker-compose up` — verify single-command local startup works cleanly

- [ ] **9.5** Prepare a 2-minute live demo script walking through Scenario B (most compelling)

---

## Team Assignment Suggestions

| Member | Primary Responsibility |
|--------|----------------------|
| Trưởng nhóm (Hoài Anh) | Pipeline wiring (Phase 6), API (Phase 7), system integration |
| Thành viên (Nam Hải) | Agent 2 OSINT (Phase 3) + Agent 3 Verifier (Phase 4) |
| Thành viên (Tiến Dũng) | Agent 1 Extractor (Phase 1) + Agent 5 Synthesizer (Phase 5) |
| Thành viên (Minh Hải) | Agent 4 RAG + index build (Phase 2) + Frontend (Phase 8) |

---

## Definition of Done (MVP)

- [ ] All 5 agents execute without error on a valid IT CV
- [ ] Contradictions are detected when OSINT data conflicts with CV
- [ ] Benchmark comparison reflects `it-domain/` corpus data
- [ ] Final report includes hire recommendation + job-fit score
- [ ] HR dashboard displays report and accepts hire/reject decision
- [ ] `docker-compose up` starts the entire system locally
- [ ] 3 demo scenarios work reliably
