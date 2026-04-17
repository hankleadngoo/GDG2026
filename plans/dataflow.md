# Data Flow — Resume Protector

## Overview

The system follows a **linear pipeline** with conditional branching at two key decision points (social links available? → OSINT; verified profile trustworthy? → proceed or email candidate). Each agent passes a structured state object to the next via the LangGraph/CrewAI graph.

---

## End-to-End Flow

```
Recruiter / HR
    │
    │  uploads CV / Resume / Portfolio (PDF, DOCX)
    ▼
┌─────────────────────────────────────────────┐
│  Agent 1 — Extractor                        │
│  backend/agents/agent1_extractor/parser.py  │
│                                             │
│  Input : raw CV file                        │
│  Tools : LlamaParse / PyMuPDF               │
│  Output: structured candidate profile       │
│           • personal info, skills, exp      │
│           • extracted social/project links  │
│             (LinkedIn, GitHub, Facebook...) │
└──────────────────┬──────────────────────────┘
                   │
          links found?
          ┌────Yes─┴────No──────────────────────┐
          ▼                                      ▼
┌─────────────────────────┐        flag: "no external links"
│  Agent 2 — OSINT        │        skip to Agent 3 with
│  agent2_osint/          │        CV-only data
│  searcher.py            │
│                         │
│  Input : links + candidate summary           │
│  Tools : Tavily / Exa.ai (web search)        │
│          Proxycurl / PDL (LinkedIn JSON)     │
│          GitHub API (commit history, repos)  │
│  Output: raw public profile data             │
│           • LinkedIn headline, endorsements  │
│           • GitHub repos, commit frequency   │
│           • any other public mentions        │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│  Agent 3 — Verifier                         │
│  agent3_verifier/checker.py                 │
│                                             │
│  Input : Agent 1 (CV claims)                │
│          Agent 2 (public data)              │
│  Logic : cross-reference & diff             │
│           • detect contradictions           │
│           • flag missing / unverifiable     │
│             claims                          │
│           • score information trust level   │
│  Output: verified consolidated profile      │
│           • confirmed facts                 │
│           • contradiction list              │
│           • trust score                     │
└──────────┬──────────────────────────────────┘
           │
    profile trustworthy?
    ┌──Yes─┴──────────────No─────────────────────┐
    ▼                                             ▼
    │                              ┌──────────────────────────┐
    │                              │  Gmail API               │
    │                              │  auto-send email to      │
    │                              │  candidate requesting    │
    │                              │  clarification /         │
    │                              │  additional proof        │
    │                              └──────────────────────────┘
    │                                (candidate may resubmit)
    │
    ▼  (runs in parallel with Agent 3 result)
┌─────────────────────────────────────────────┐
│  Agent 4 — RAG Benchmarker                  │
│  agent4_rag/retriever.py                    │
│                                             │
│  Input : job role / JD keywords             │
│  Tools : FAISS (dev) /                      │
│          Vertex AI Vector Search (prod)     │
│          Google Text Embedding API          │
│  Data  : data/all-domains/ (1 291 PDFs)     │
│          data/it-domain/   (649 IT PDFs)    │
│  Logic : embed JD → similarity search →     │
│          retrieve top-K similar historical  │
│          CVs → aggregate skill/exp stats    │
│  Output: industry benchmark profile         │
│           • average years of exp per skill  │
│           • common skill set for the role   │
│           • score distribution              │
└──────────┬──────────────────────────────────┘
           │
           ▼  (merged with Agent 3 output)
┌─────────────────────────────────────────────┐
│  Agent 5 — Synthesizer                      │
│  agent5_synthesizer/reporter.py             │
│                                             │
│  Input : Agent 3 (verified profile)         │
│          Agent 4 (benchmark data)           │
│  LLM   : Gemini 1.5 Pro                     │
│  Output: final assessment report            │
│           • skill gap analysis              │
│           • percentile vs industry avg      │
│           • job-fit score (0–100)           │
│           • hire / no-hire recommendation   │
│           • caveats / pipeline anomalies    │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│  HR Dashboard (Frontend)                    │
│  Recruiter reviews report + makes           │
│  final hire / reject decision               │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│  Feedback Loop (Self-learning)              │
│  HR decision → stored in Vector DB          │
│  Future Agent 4 queries incorporate         │
│  historical hiring outcomes as weights      │
└─────────────────────────────────────────────┘
```

---

## State Object Passed Between Agents

```python
AgentState = {
    # Set by Agent 1
    "cv_raw_text": str,
    "candidate_profile": dict,   # name, email, skills, experience, education
    "extracted_links": list[str],

    # Set by Agent 2
    "osint_data": dict,          # keyed by platform (linkedin, github, ...)
    "osint_status": str,         # "success" | "partial" | "skipped"

    # Set by Agent 3
    "verified_profile": dict,
    "contradictions": list[dict],
    "trust_score": float,        # 0.0–1.0
    "email_sent": bool,

    # Set by Agent 4
    "benchmark": dict,           # industry avg stats for the target role
    "similar_cvs_retrieved": int,

    # Set by Agent 5
    "final_report": dict,        # full assessment
    "hire_recommendation": bool,
    "pipeline_warnings": list[str],
}
```

---

## Fallback / Exception Handling per Agent

| Agent | Failure Condition | Fallback Behavior |
|-------|------------------|-------------------|
| Agent 1 | Unparseable PDF/DOCX | Return partial extraction; flag to HR |
| Agent 2 | API rate-limit / profile private | Skip OSINT; mark `osint_status = "skipped"` |
| Agent 3 | No OSINT data available | Verify CV internally only; lower trust_score |
| Agent 4 | No similar CVs found | Use global average; flag "insufficient benchmark data" |
| Agent 5 | Incomplete inputs | Produce partial report with explicit caveats |

Every pipeline anomaly is surfaced in `pipeline_warnings` in the final report shown to HR.

---

## Data Storage

| Data Type | Storage | Notes |
|-----------|---------|-------|
| Uploaded CV files | Google Cloud Storage | Retained for audit |
| Candidate & HR session state | PostgreSQL (Cloud SQL) | Interview round tracking |
| CV embeddings (historical) | FAISS (dev) / Vertex AI Vector Search (prod) | Used by Agent 4 |
| User auth | Firebase Authentication | Recruiter login |
| HR hiring decisions (feedback) | Vector DB + PostgreSQL | Feeds self-learning loop |

