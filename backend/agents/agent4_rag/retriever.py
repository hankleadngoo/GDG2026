"""
retriever.py — Agent 4: Competitive Profiler
=============================================

Two public functions:

    ingest_candidate(state)  →  None
        Embeds a raw CV and upserts it into Qdrant (called after Agent 1).

    run_agent4(state)  →  dict
        Aggregates the talent pool and computes the candidate's competitive
        percentile (called after Agent 3).

Environment variables (loaded from .env):
    GOOGLE_API_KEY   — Gemini + Google Text Embedding API
    QDRANT_URL       — e.g. http://localhost:6333
    QDRANT_API_KEY   — empty for local dev, required for Qdrant Cloud
    BATCH_ID         — e.g. GDGOC_Hackathon_2026
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections import Counter
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from .schema import CandidatePayload

# ── Bootstrap ─────────────────────────────────────────────────────────────────

load_dotenv()

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

COLLECTION_NAME = "resumes"
EMBEDDING_MODEL = "models/text-embedding-004"
EMBEDDING_DIM = 768          # fixed dimension for text-embedding-004
EXTRACTION_MODEL = "gemini-1.5-flash"
SMALL_POOL_THRESHOLD = 5
COMMON_SKILL_RATIO = 0.30    # skill must appear in ≥30 % of pool CVs

# ── Qdrant client (module-level singleton) ────────────────────────────────────

_qdrant_client: QdrantClient | None = None


def _get_client() -> QdrantClient:
    """Return (and lazily create) the module-level Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY") or None  # None = no auth (local dev)
        _qdrant_client = QdrantClient(url=url, api_key=api_key, timeout=10)
        _ensure_collection(_qdrant_client)
    return _qdrant_client


def _ensure_collection(client: QdrantClient) -> None:
    """Create the `resumes` collection if it does not exist yet."""
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qdrant_models.VectorParams(
                size=EMBEDDING_DIM,
                distance=qdrant_models.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection '%s'.", COLLECTION_NAME)


# ── Google GenAI client ───────────────────────────────────────────────────────

def _get_genai_client() -> genai.Client:
    api_key = os.environ["GOOGLE_API_KEY"]
    return genai.Client(api_key=api_key)


# ── Embedding helper ──────────────────────────────────────────────────────────

def _embed_text(text: str) -> list[float]:
    """
    Embed *text* using Google Text Embedding API (text-embedding-004).
    Returns a 768-dimensional float list.
    Raises on API error — caller is responsible for catching.
    """
    client = _get_genai_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
        ),
    )
    return response.embeddings[0].values


# ── Payload extraction helper ─────────────────────────────────────────────────

_EXTRACTION_PROMPT = """\
Extract structured information from the CV text below and return ONLY a valid
JSON object with exactly these keys (no markdown fences, no extra text):

{{
  "job_title": "<primary target role the candidate is applying for, or most recent title>",
  "years_of_experience": <float, total professional years>,
  "skills": {{
    "core": ["<skill1>", "<skill2>", ...],
    "tools": ["<tool1>", "<tool2>", ...]
  }},
  "education": {{
    "level": "<one of: High School | Associate | Undergraduate | Master | PhD>",
    "major": "<field of study>"
  }}
}}

CV TEXT:
{cv_text}
"""


def _extract_payload_from_text(
    cv_text: str,
    candidate_id: str,
    batch_id: str,
) -> CandidatePayload | None:
    """
    Call Gemini Flash to parse raw CV text into a CandidatePayload.
    Returns None on any failure (caller appends a warning instead of crashing).
    """
    try:
        client = _get_genai_client()
        prompt = _EXTRACTION_PROMPT.format(cv_text=cv_text[:8000])  # cap token usage
        response = client.models.generate_content(
            model=EXTRACTION_MODEL,
            contents=prompt,
        )
        raw = response.text.strip()
        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        data["candidate_id"] = candidate_id
        data["batch_id"] = batch_id
        return CandidatePayload.from_dict(data)
    except Exception as exc:
        logger.warning("Payload extraction failed: %s", exc)
        return None


# ── Public function 1: Ingest ─────────────────────────────────────────────────

def ingest_candidate(state: dict[str, Any]) -> None:
    """
    Embed the candidate's raw CV and upsert it into the Qdrant talent pool.

    Reads from state:
        state["cv_raw_text"]     — full CV text produced by Agent 1
        state["candidate_id"]    — optional; generated if missing
        state["pipeline_warnings"] — list to append warnings to

    Writes nothing back to state (side-effect only: Qdrant upsert).
    """
    warnings: list[str] = state.setdefault("pipeline_warnings", [])
    cv_text: str = state.get("cv_raw_text", "").strip()
    candidate_id: str = state.get("candidate_id") or str(uuid.uuid4())
    batch_id: str = os.getenv("BATCH_ID", "default_batch")

    if not cv_text:
        warnings.append("agent4: skipped ingestion — cv_raw_text is empty")
        return

    # 1. Extract structured payload via Gemini
    payload = _extract_payload_from_text(cv_text, candidate_id, batch_id)
    if payload is None:
        warnings.append(
            "agent4: skipped ingestion — Gemini payload extraction failed"
        )
        return

    # 2. Embed the raw CV text
    try:
        vector = _embed_text(cv_text)
    except Exception as exc:
        warnings.append(f"agent4: skipped ingestion — embedding error: {exc}")
        return

    # 3. Upsert into Qdrant
    try:
        client = _get_client()
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                qdrant_models.PointStruct(
                    id=candidate_id,
                    vector=vector,
                    payload=payload.to_dict(),
                )
            ],
        )
        logger.info(
            "Ingested candidate %s (%s) into Qdrant.",
            candidate_id,
            payload.job_title,
        )
    except Exception as exc:
        warnings.append(f"agent4: Qdrant upsert failed: {exc}")


# ── Public function 2: Benchmark ──────────────────────────────────────────────

def run_agent4(state: dict[str, Any]) -> dict[str, Any]:
    """
    Aggregate the talent pool for the target role and compute competitive
    benchmarks for the current candidate.

    Reads from state:
        state["candidate_profile"]["target_role"]
        state["candidate_profile"]["skills"]        — list[str]
        state["candidate_profile"]["years_of_experience"]
        state["pipeline_warnings"]

    Writes to state (and returns the updated state dict):
        state["benchmark"]               — pool stats + candidate percentiles
        state["similar_cvs_retrieved"]  — equals pool_size
    """
    warnings: list[str] = state.setdefault("pipeline_warnings", [])
    profile: dict = state.get("candidate_profile", {})
    target_role: str = profile.get("target_role", "")
    candidate_skills: list[str] = profile.get("skills", [])
    candidate_exp: float = float(profile.get("years_of_experience", 0.0))
    batch_id: str = os.getenv("BATCH_ID", "default_batch")

    empty_benchmark: dict[str, Any] = {
        "pool_size": 0,
        "avg_years_experience": None,
        "common_skills": [],
        "education_distribution": {},
        "candidate_exp_percentile": None,
        "candidate_skill_match_score": None,
    }

    # ── Fetch pool from Qdrant ────────────────────────────────────────────────
    try:
        client = _get_client()
        pool_points = _scroll_all(client, target_role, batch_id)
    except Exception as exc:
        warnings.append(f"agent4: benchmark unavailable — Qdrant connection failed: {exc}")
        state["benchmark"] = empty_benchmark
        state["similar_cvs_retrieved"] = 0
        return state

    pool_size = len(pool_points)

    # ── Edge cases ────────────────────────────────────────────────────────────
    if pool_size == 0:
        warnings.append(
            "agent4: no benchmark data — candidate is first in pool"
        )
        state["benchmark"] = empty_benchmark
        state["similar_cvs_retrieved"] = 0
        return state

    if pool_size < SMALL_POOL_THRESHOLD:
        warnings.append(
            f"agent4: small talent pool (n={pool_size}); benchmark may be unreliable"
        )

    # ── Aggregate ─────────────────────────────────────────────────────────────
    exp_values: list[float] = []
    skill_counter: Counter = Counter()
    edu_counter: Counter = Counter()

    for point in pool_points:
        p = point.payload or {}
        exp = float(p.get("years_of_experience", 0.0))
        exp_values.append(exp)

        skills_dict = p.get("skills", {})
        for skill in skills_dict.get("core", []):
            skill_counter[skill] += 1

        edu_level = p.get("education", {}).get("level", "Unknown")
        edu_counter[edu_level] += 1

    avg_exp = sum(exp_values) / pool_size
    common_skills = [
        skill
        for skill, count in skill_counter.items()
        if count / pool_size >= COMMON_SKILL_RATIO
    ]
    education_distribution = dict(edu_counter)

    # ── Candidate percentile ──────────────────────────────────────────────────
    # exp_percentile: fraction of pool with exp <= candidate's
    exp_percentile = sum(1 for e in exp_values if e <= candidate_exp) / pool_size

    # skill_match_score: overlap with common skills (0.0 if no common skills)
    if common_skills:
        candidate_skill_set = {s.lower() for s in candidate_skills}
        common_skill_set = {s.lower() for s in common_skills}
        skill_match_score = len(candidate_skill_set & common_skill_set) / len(common_skill_set)
    else:
        skill_match_score = 0.0

    # ── Write back ────────────────────────────────────────────────────────────
    benchmark = {
        "pool_size": pool_size,
        "avg_years_experience": round(avg_exp, 2),
        "common_skills": sorted(common_skills),
        "education_distribution": education_distribution,
        "candidate_exp_percentile": round(exp_percentile, 4),
        "candidate_skill_match_score": round(skill_match_score, 4),
    }

    state["benchmark"] = benchmark
    state["similar_cvs_retrieved"] = pool_size

    logger.info(
        "Agent 4 benchmark: pool_size=%d, exp_pct=%.2f, skill_match=%.2f",
        pool_size,
        exp_percentile,
        skill_match_score,
    )
    return state


# ── Internal: paginated scroll ────────────────────────────────────────────────

def _scroll_all(
    client: QdrantClient,
    job_title: str,
    batch_id: str,
) -> list[Any]:
    """
    Paginate through all Qdrant points where
        payload.job_title == job_title  AND  payload.batch_id == batch_id.

    Returns a flat list of ScoredPoint / Record objects (whatever scroll gives).
    """
    scroll_filter = qdrant_models.Filter(
        must=[
            qdrant_models.FieldCondition(
                key="job_title",
                match=qdrant_models.MatchValue(value=job_title),
            ),
            qdrant_models.FieldCondition(
                key="batch_id",
                match=qdrant_models.MatchValue(value=batch_id),
            ),
        ]
    )

    all_points: list[Any] = []
    next_offset = None

    while True:
        results, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=scroll_filter,
            limit=100,
            offset=next_offset,
            with_payload=True,
            with_vectors=False,
        )
        all_points.extend(results)
        if next_offset is None:
            break

    return all_points
