# Plan: Agent 4 — The Competitive Profiler

## Context

Agent 4 answers one question: **"In the pool of all CVs submitted for this role, where does this candidate rank?"**

Unlike the previous plan (offline FAISS + K-NN retrieval), the updated design uses **Qdrant** as a real-time vector database with structured payloads. Every CV processed by Agent 1 is immediately upserted into Qdrant. Agent 4 then runs **aggregation queries** over the entire talent pool filtered by `job_title` and `batch_id` — rather than finding nearest neighbors — to produce objective, pool-relative benchmarks.

Agent 4 has two distinct responsibilities:
1. **Ingestion** — after Agent 1 completes, upsert the candidate's vector + structured payload into Qdrant
2. **Benchmarking** — aggregate stats from the full talent pool and compute the candidate's competitive percentile

---

## Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Vector DB | **Qdrant** | Native payload filtering + aggregation; replaces FAISS |
| Qdrant mode (dev) | In-memory / local Docker | Free, no cloud needed for dev |
| Qdrant mode (prod) | Qdrant Cloud or self-hosted | Scalable, persistent |
| PDF Parser | PyMuPDF (`fitz`) | Free, offline, no API key needed |
| Embedding model | Google Text Embedding API `models/text-embedding-004` | Already in stack |
| Extraction LLM | `gemini-1.5-flash` | Cheap, used to parse raw CV text → structured payload |
| Collection name | `resumes` | Single collection, filtered by `job_title` + `batch_id` |

---

## Qdrant Point Payload Schema

Each point in the Qdrant `resumes` collection stores:

```json
{
  "candidate_id": "uuid-string",
  "job_title": "Data Scientist",
  "batch_id": "GDGOC_Hackathon_2026",
  "years_of_experience": 1.5,
  "skills": {
    "core": ["Python", "Machine Learning", "SQL"],
    "tools": ["Git", "Docker"]
  },
  "education": {
    "level": "Undergraduate",
    "major": "Data Science"
  }
}
```

The **vector** stored alongside the payload is the embedding of the full CV text (from Agent 1's `cv_raw_text`).

---

## Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/requirements.txt` | **Write** | Add dependencies |
| `backend/agents/agent4_rag/__init__.py` | **Create** | Package init |
| `backend/agents/agent4_rag/retriever.py` | **Write** | Ingestion + aggregation + benchmarking logic |
| `backend/agents/agent4_rag/schema.py` | **Create** | Payload dataclass + validation |
| `docker-compose.yml` | **Update** | Add Qdrant service for local dev |
| `.env.example` | **Update** | Add `GOOGLE_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `BATCH_ID` |

---

## Step 1 — `backend/requirements.txt`

Add:
```
pymupdf==1.24.5
qdrant-client==1.9.1
google-generativeai==0.7.2
python-dotenv==1.0.1
tqdm==4.66.4
numpy==1.26.4
```

---

## Step 2 — `docker-compose.yml` (add Qdrant service)

```yaml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
  volumes:
    - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
```

Local Qdrant URL: `http://localhost:6333`

---

## Step 3 — `backend/agents/agent4_rag/schema.py`

Defines the structured payload dataclass used for ingestion and type safety:

```python
@dataclass
class CandidatePayload:
    candidate_id: str
    job_title: str
    batch_id: str
    years_of_experience: float
    skills: dict        # {"core": [...], "tools": [...]}
    education: dict     # {"level": str, "major": str}
```

---

## Step 4 — `backend/agents/agent4_rag/retriever.py`

### Module-level setup
- Load `.env` with `python-dotenv`
- Initialize `QdrantClient` (URL + API key from env)
- Ensure collection `resumes` exists on startup (create if missing, with correct vector size 768 for `text-embedding-004`)

### Two public functions

---

#### `ingest_candidate(state: dict) -> None`

Called immediately after Agent 1 finishes (before Agents 2 & 3 run). Inserts the current candidate into Qdrant so the talent pool stays up to date.

**Steps:**
1. Extract `cv_raw_text` from state
2. Call `gemini-1.5-flash` to parse raw text → structured `CandidatePayload` JSON:
   - `job_title`, `years_of_experience`, `skills.core`, `skills.tools`, `education.level`, `education.major`
3. Embed `cv_raw_text` → vector via Google Text Embedding API (`RETRIEVAL_DOCUMENT`)
4. Upsert point into Qdrant:
   - `id`: `candidate_id` (from state or generate UUID)
   - `vector`: embedding
   - `payload`: `CandidatePayload` dict + `batch_id` from env

---

#### `run_agent4(state: dict) -> dict`

Called during the pipeline (after Agent 3). Aggregates the talent pool and produces the competitive benchmark.

**Input** (from `AgentState`):
```python
state["candidate_profile"]["target_role"]    # job title to filter pool by
state["candidate_profile"]["skills"]         # candidate's own skills
state["candidate_profile"]["years_of_experience"]
state["pipeline_warnings"]
```

**Processing steps:**

```
1. Filter Qdrant collection:
   Filter: job_title == target_role AND batch_id == BATCH_ID
   → Scroll all matching points (paginated if large pool)

2. Aggregate over the pool:
   - avg_years_experience    = mean(payload.years_of_experience for all points)
   - skill_frequency         = Counter of all core skills across pool
   - common_skills           = skills present in ≥ 30% of pool CVs
   - education_distribution  = Counter of payload.education.level

3. Compute candidate's competitive percentile:
   - exp_percentile: % of pool with years_of_experience ≤ candidate's
   - skill_match_score: (candidate skills ∩ common_skills) / len(common_skills)

4. Build benchmark dict and write to state
```

**Output** (writes back to `AgentState`):
```python
state["benchmark"] = {
    "pool_size": int,                      # total CVs in this job_title + batch
    "avg_years_experience": float,
    "common_skills": list[str],            # skills in ≥ 30% of pool
    "education_distribution": dict,        # {"Undergraduate": N, "Master": N, ...}
    "candidate_exp_percentile": float,     # e.g. 0.72 = top 28%
    "candidate_skill_match_score": float,  # 0.0–1.0
}
state["similar_cvs_retrieved"] = int      # = pool_size
```

---

## Data Flow (Agent 4)

```
After Agent 1:
  cv_raw_text
      │
      ├─► gemini-1.5-flash ──► CandidatePayload (structured)
      ├─► Google Embedding API ──► vector
      └─► Qdrant upsert (vector + payload)
                │
                ▼
         Qdrant collection "resumes"
         (grows with each new CV)

During pipeline (after Agent 3):
  state["candidate_profile"]
      │ target_role, skills, years_of_experience
      ▼
  Qdrant scroll + filter
  (job_title == target_role AND batch_id == BATCH_ID)
      │
      ▼
  Aggregate pool stats
      │
      ▼
  Compute percentile + skill match score
      │
      ▼
  state["benchmark"]
  state["similar_cvs_retrieved"]
```

---

## Fallback / Exception Handling

| Condition | Behavior |
|-----------|----------|
| Qdrant not reachable | Log error; append `"benchmark unavailable: Qdrant connection failed"` to `pipeline_warnings`; return empty benchmark |
| Pool is empty (first CV ever) | Append `"no benchmark data: candidate is first in pool"` to `pipeline_warnings`; return empty benchmark |
| Pool size < 5 | Append `"small talent pool (n={n})"` to `pipeline_warnings`; proceed with available data |
| Gemini payload extraction fails | Append warning; skip ingestion for this candidate; continue pipeline |
| Google Embedding API error | Append warning; skip ingestion; continue pipeline |

---

## `.env.example` additions

```bash
GOOGLE_API_KEY=          # Gemini + Text Embedding API
QDRANT_URL=http://localhost:6333   # Local dev; replace with Qdrant Cloud URL in prod
QDRANT_API_KEY=          # Leave empty for local dev; required for Qdrant Cloud
BATCH_ID=GDGOC_Hackathon_2026     # Identifies the current recruitment batch
```

---

## Verification

### 1. Start Qdrant locally
```bash
docker-compose up qdrant
# ✅ Qdrant dashboard: http://localhost:6333/dashboard
```

### 2. Test ingestion (standalone)
```bash
python -c "
import sys; sys.path.insert(0, 'backend')
from agents.agent4_rag.retriever import ingest_candidate
state = {
    'candidate_id': 'test-001',
    'cv_raw_text': 'John Doe. Software Engineer. 3 years Python, FastAPI, Docker. BSc Computer Science.',
    'pipeline_warnings': []
}
ingest_candidate(state)
print('Ingestion OK')
"
# ✅ Check Qdrant dashboard → resumes collection has 1 point
```

### 3. Test benchmarking (after ingesting several CVs)
```bash
python -c "
import sys; sys.path.insert(0, 'backend')
from agents.agent4_rag.retriever import run_agent4
state = {
    'candidate_profile': {
        'target_role': 'Software Engineer',
        'skills': ['Python', 'FastAPI'],
        'years_of_experience': 3
    },
    'pipeline_warnings': []
}
result = run_agent4(state)
print(result['benchmark'])
"
# ✅ Expected: pool_size > 0, percentile computed, common_skills populated
```

### 4. Unit tests
File: `backend/tests/agents/agent4_rag/test_retriever.py`

| Test | Mock | Assert |
|------|------|--------|
| `test_ingest_upserts_to_qdrant` | Mock Qdrant client + embedding API | `qdrant.upsert` called with correct payload schema |
| `test_benchmark_aggregates_pool` | Qdrant scroll → 10 mock points | `avg_years_experience` correct, `common_skills` reflects ≥30% threshold |
| `test_percentile_computation` | Pool of 10 with known exp values | Candidate with 3yr exp in pool of [1,2,3,4,5] → `exp_percentile == 0.6` |
| `test_fallback_empty_pool` | Qdrant scroll → 0 results | `pipeline_warnings` contains "first in pool", empty benchmark returned |
| `test_fallback_qdrant_unreachable` | Qdrant client raises `ConnectionError` | `pipeline_warnings` contains "connection failed", no crash |
| `test_fallback_small_pool` | Qdrant scroll → 3 results | `pipeline_warnings` contains "small talent pool" |
