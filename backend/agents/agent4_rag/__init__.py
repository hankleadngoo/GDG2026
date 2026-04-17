"""
agent4_rag — Competitive Profiler agent package.

Public API
----------
ingest_candidate(state)  →  None
    Called right after Agent 1 finishes.  Embeds the raw CV text and upserts
    a structured point into the Qdrant `resumes` collection so the talent
    pool stays up-to-date in real time.

run_agent4(state)  →  dict
    Called during the main pipeline (after Agent 3).  Aggregates pool stats
    for the target role / batch and writes competitive benchmarks back into
    the pipeline state.
"""

from .retriever import ingest_candidate, run_agent4

__all__ = ["ingest_candidate", "run_agent4"]
