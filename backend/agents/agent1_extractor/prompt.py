"""
Prompts for Agent 1 — CV Extractor.

Gemini is called with:
  - system_instruction = SYSTEM_PROMPT  (sets the role and rules)
  - user message       = build_user_prompt(raw_text, job_description)

The model is configured with response_mime_type="application/json" so the
response is guaranteed to be valid JSON matching the CVExtraction schema.
"""

from __future__ import annotations

import json

from backend.agents.agent1_extractor.schema import CVExtraction

# ---------------------------------------------------------------------------
# System prompt — injected once per Gemini session / generate_content call
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a precise CV / resume information extractor.

Your job is to read a CV and return a single JSON object that follows the schema provided exactly.

Rules you MUST follow:
1. Extract ONLY information explicitly present in the CV text. Do NOT infer, invent, or hallucinate any field.
2. If a field is not present in the CV, output null (for scalar fields) or [] (for arrays).
3. Preserve URLs exactly as written — do not normalise, shorten, or expand them.
4. For dates, preserve the format as written (e.g. "Jan 2022", "2022-01", "2022"). Do not convert.
5. Split skills into the correct category: languages = programming/markup languages only; frameworks = libraries/frameworks; tools = software tools, platforms, services; other = everything else.
6. If the candidate lists the same URL in multiple places, include it only once in the most specific field (e.g. a GitHub link goes into social_links.github, not into other).
7. The output must be valid JSON parseable by Python's json.loads() with no trailing commas or comments.
"""

# ---------------------------------------------------------------------------
# JSON schema embedded in the user prompt
# ---------------------------------------------------------------------------

_SCHEMA_JSON = json.dumps(CVExtraction.model_json_schema(), indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------


def build_user_prompt(raw_cv_text: str, job_description: str | None = None) -> str:
    """
    Build the user-turn prompt that is sent to Gemini together with the system prompt.

    Args:
        raw_cv_text:      Plain text extracted from the CV (by LlamaParse / docx / raw).
        job_description:  Optional job description text. When provided, tells the model
                          to flag skills and experience particularly relevant to the role
                          inside the existing fields (no extra keys are added).
    """
    jd_section = ""
    if job_description and job_description.strip():
        jd_section = f"""
---
JOB DESCRIPTION (for context only — use it to understand relevance, NOT to add information not in the CV):
{job_description.strip()}
---
"""

    return f"""Extract all information from the CV below and return it as a JSON object.

The JSON must strictly match this schema:
```json
{_SCHEMA_JSON}
```
{jd_section}
---
CV TEXT:
{raw_cv_text.strip()}
---

Return ONLY the JSON object. No markdown fences, no explanation, no preamble."""


# ---------------------------------------------------------------------------
# Retry prompt — used when the first response fails JSON validation
# ---------------------------------------------------------------------------


def build_retry_prompt(raw_cv_text: str, previous_response: str, error_msg: str) -> str:
    """
    Called by parser.py when Gemini returns malformed JSON on the first attempt.
    Feeds the error back to the model for a self-correction pass.
    """
    return f"""Your previous response could not be parsed as valid JSON.

Error: {error_msg}

Your previous (broken) response:
{previous_response[:2000]}

Please return a corrected, valid JSON object matching the schema below. No markdown, no explanation.

Schema:
```json
{_SCHEMA_JSON}
```

CV TEXT (same as before):
{raw_cv_text.strip()}"""
