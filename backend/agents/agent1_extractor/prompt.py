"""
prompt.py — Prompts for Agent 1 (CV Extractor).

Gemini is called with:
  - system_instruction = SYSTEM_PROMPT  (sets the role and rules)
  - user message       = build_user_prompt(raw_text, job_description)
"""

from __future__ import annotations

# ── System Prompt ─────────────────────────────────────────────────────────────

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
6. Return ONLY valid JSON. No preamble, no explanation, no markdown formatting."""

# ── JSON Schema String ────────────────────────────────────────────────────────

_SCHEMA_JSON = '''{
  "candidate": {
    "full_name": "string",
    "email": "string | null",
    "phone": "string | null",
    "location": "string | null",
    "summary": "string | null"
  },
  "metadata": {
    "source_file": "string",
    "parse_method": "string",
    "extraction_model": "string",
    "extracted_at": "string",
    "warnings": ["string"]
  },
  "social_links": {
    "linkedin": "string | null",
    "github": "string | null",
    "facebook": "string | null",
    "portfolio": "string | null",
    "other": ["string"]
  },
  "education": [
    {
      "institution": "string",
      "degree": "string | null",
      "major": "string | null",
      "gpa": "string | null",
      "start_year": "integer | null",
      "end_year": "integer | null"
    }
  ],
  "work_experience": [
    {
      "company": "string",
      "role": "string",
      "start_date": "string | null",
      "end_date": "string | null",
      "is_current": "boolean",
      "responsibilities": ["string"],
      "company_url": "string | null"
    }
  ],
  "projects": [
    {
      "name": "string",
      "description": "string | null",
      "tech_stack": ["string"],
      "links": {
        "github": "string | null",
        "demo": "string | null",
        "other": ["string"]
      },
      "role": "string | null"
    }
  ],
  "skills": {
    "languages": ["string"],
    "frameworks": ["string"],
    "tools": ["string"],
    "other": ["string"]
  },
  "certifications": [
    {
      "name": "string",
      "issuer": "string | null",
      "year": "integer | null",
      "url": "string | null"
    }
  ],
  "languages_spoken": [
    {
      "language": "string",
      "proficiency": "string | null"
    }
  ]
}'''

# ── Prompt Builders ───────────────────────────────────────────────────────────

def build_user_prompt(raw_cv_text: str, job_description: str | None = None) -> str:
    """
    Build the user-turn prompt that is sent to Gemini together with the system prompt.
    """
    jd_section = ""
    if job_description and job_description.strip():
        jd_section = (
            "\n---\n"
            "JOB DESCRIPTION (for context only — use it to understand relevance, NOT to add information not in the CV):\n"
            f"{job_description.strip()}\n"
            "---\n"
        )

    return (
        "Extract all information from the CV below and return it as a JSON object.\n\n"
        "The JSON must strictly match this schema:\n"
        f"{_SCHEMA_JSON}\n"
        f"{jd_section}\n"
        "---\n"
        "CV TEXT:\n"
        f"{raw_cv_text.strip()}\n"
        "---\n\n"
        "Return ONLY the JSON object. No explanation, no preamble."
    )


def build_retry_prompt(raw_cv_text: str, previous_response: str, error_msg: str) -> str:
    """
    Called by the parser when Gemini returns malformed JSON on the first attempt.
    Feeds the error back to the model for a self-correction pass.
    """
    return (
        "Your previous response could not be parsed as valid JSON.\n\n"
        f"Error: {error_msg}\n\n"
        "Your previous (broken) response:\n"
        f"{previous_response[:2000]}\n\n"
        "Please return a corrected, valid JSON object matching the schema below. No explanation.\n\n"
        "Schema:\n"
        f"{_SCHEMA_JSON}\n\n"
        "CV TEXT (same as before):\n"
        f"{raw_cv_text.strip()}"
    )