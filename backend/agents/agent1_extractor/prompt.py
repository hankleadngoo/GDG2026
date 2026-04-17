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

# backend/agents/agent1_extractor/prompt.py

SYSTEM_PROMPT = """You are a precise CV / resume information extractor.

Your job is to read a CV and return a single JSON object that follows the schema provided exactly.

### RULES FOR HYPERLINKS & METADATA:
1. The CV text may contain a section labeled 'DETECTED HYPERLINKS' or 'EXTRACTED HYPERLINKS (METADATA)'. 
2. Use these URLs to fill fields like social_links (LinkedIn, GitHub, Portfolio) even if the URL is not written inline next to the text.
3. If the text says "LinkedIn" or "GitHub" and you find a corresponding URL in the metadata section, map them together.
4. Preserve URLs exactly as written — do not normalise, shorten, or expand them.

### GENERAL RULES:
1. Extract ONLY information explicitly present in the CV text or metadata. Do NOT infer, invent, or hallucinate.
2. If a field is not present, output null (for scalar fields) or [] (for arrays).
3. For dates, preserve the format as written (e.g. "Jan 2022", "2022-01"). Do not convert.
4. Split skills accurately: 
   - languages: programming/markup languages only (e.g., Python, Java).
   - frameworks: libraries/frameworks (e.g., PyTorch, TensorFlow, Keras).
   - tools: software tools, platforms (e.g., Git, Docker, Hugging Face).
   - other: soft skills or categories not fitting above.
5. If a URL appears in multiple places, include it only once in the most specific field.
6. Return ONLY valid JSON. No markdown fences, no preamble, no explanation.
"""

# Các phần còn lại (build_user_prompt, build_retry_prompt) giữ nguyên cấu trúc cũ của bạn 
# vì chúng đã truyền raw_cv_text (đã bao gồm phần Metadata link mà chúng ta đã sửa ở parser.py).

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
