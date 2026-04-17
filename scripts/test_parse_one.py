"""
scripts/test_parse_one.py
--------------------------
Test extraction on a single CV PDF:
  1. Try pdfplumber (free, offline, great for text-based PDFs)
  2. If empty → fallback to Gemini 1.5 Flash vision (for image/scanned PDFs)

Outputs structured JSON matching the Qdrant payload schema.

Usage (from repo root, with venv activated):
    python scripts/test_parse_one.py
    python scripts/test_parse_one.py data/it-domain/<filename>.pdf
"""

import sys
import json
import os
from pathlib import Path

import pdfplumber
from dotenv import load_dotenv

# Fix Windows terminal encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

REPO_ROOT   = Path(__file__).parent.parent
DEFAULT_PDF = REPO_ROOT / "data" / "it-domain" / "003ada45-7271-4e1d-8d61-6f5b5542b3d7.pdf"
OUTPUT_DIR  = REPO_ROOT / "data" / "it-domain-md"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ---------------------------------------------------------------------------
# Gemini prompt
# ---------------------------------------------------------------------------
EXTRACT_PROMPT = """You are an expert HR analyst. Extract structured information from this CV/resume.

Return ONLY a valid JSON object with this exact schema (no markdown, no explanation):
{
  "full_name": "string or null",
  "job_title": "string — the most recent or target job title (in English)",
  "years_of_experience": float — total years of professional experience (0 if student/fresher),
  "skills": {
    "core": ["list of primary technical skills, languages, frameworks"],
    "tools": ["list of tools, platforms, databases, DevOps, cloud"]
  },
  "education": {
    "level": "one of: High School | Undergraduate | Graduate | Postgraduate | Other",
    "major": "field of study in English or null"
  },
  "language": "one of: Vietnamese | English | Bilingual"
}

Rules:
- job_title must be in English (translate if needed), e.g. "Software Engineer", "Data Scientist"
- years_of_experience: calculate from work history dates; if only internship → 0.5; if fresher → 0
- skills.core: programming languages, frameworks, main technologies (e.g. Python, React, Machine Learning)
- skills.tools: supporting tools (e.g. Git, Docker, MySQL, AWS, Figma)
- Keep all skill names in English
- If a field cannot be determined, use null
"""

# ---------------------------------------------------------------------------
# Step 1: Extract text with pdfplumber
# ---------------------------------------------------------------------------

def extract_text_pdfplumber(pdf_path: Path) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        pages = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
    return "\n\n".join(pages)


# ---------------------------------------------------------------------------
# Gemini client (new google-genai SDK)
# ---------------------------------------------------------------------------

def get_gemini_client():
    try:
        from google import genai
        from google.genai import types  # noqa: F401 — ensure SDK is complete
    except ImportError:
        sys.exit("[ERROR] Run: pip install google-genai")
    if not GOOGLE_API_KEY:
        sys.exit("[ERROR] GOOGLE_API_KEY not set in .env")
    return genai.Client(api_key=GOOGLE_API_KEY)


# ---------------------------------------------------------------------------
# Step 2: Fallback — Gemini 1.5 Flash vision
# ---------------------------------------------------------------------------

def extract_text_gemini_vision(pdf_path: Path) -> str:
    """Convert PDF pages to images and send to Gemini 1.5 Flash vision."""
    try:
        import fitz          # PyMuPDF
        from PIL import Image
        import io
    except ImportError:
        print("[WARN] pymupdf / Pillow not installed — cannot use vision fallback")
        return ""

    client = get_gemini_client()

    doc = fitz.open(str(pdf_path))
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        images.append(img)
    doc.close()

    if not images:
        return ""

    print(f"  [VISION] Sending {len(images)} page(s) to Gemini 1.5 Flash vision...")
    from google.genai import types
    parts = ["Extract ALL text from this CV exactly as written, preserving structure:"]
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        parts.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"))

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=parts,
    )
    return response.text


# ---------------------------------------------------------------------------
# Step 3: Parse text → structured JSON via Gemini
# ---------------------------------------------------------------------------

def extract_structured(raw_text: str) -> dict:
    client = get_gemini_client()

    prompt = EXTRACT_PROMPT + f"\n\nCV TEXT:\n{raw_text}"
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )

    raw = response.text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse Gemini JSON response: {e}")
        print(f"[RAW RESPONSE]\n{raw}")
        return {}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_pdf(pdf_path: Path) -> dict | None:
    print(f"\n[FILE] {pdf_path.name}")
    print("-" * 60)

    # Step 1: pdfplumber
    raw_text = extract_text_pdfplumber(pdf_path)
    if len(raw_text.strip()) > 100:
        print(f"  [pdfplumber] Extracted {len(raw_text)} chars")
        method = "pdfplumber"
    else:
        print(f"  [pdfplumber] Too short ({len(raw_text)} chars) — using Gemini vision fallback")
        raw_text = extract_text_gemini_vision(pdf_path)
        method = "gemini_vision"
        if not raw_text:
            print("  [ERROR] Both methods failed — skipping")
            return None

    # Step 2: Gemini structured extraction
    print(f"  [Gemini] Extracting structured data...")
    structured = extract_structured(raw_text)
    if not structured:
        return None

    # Add metadata
    structured["candidate_id"] = pdf_path.stem
    structured["batch_id"]     = os.getenv("BATCH_ID", "GDGOC_Hackathon_2026")
    structured["source_file"]  = pdf_path.name
    structured["parse_method"] = method

    return structured


def main():
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF

    if not pdf_path.exists():
        sys.exit(f"[ERROR] File not found: {pdf_path}")

    result = process_pdf(pdf_path)

    if not result:
        print("\n[FAILED] No structured data extracted.")
        sys.exit(1)

    # Pretty print
    print("\n" + "=" * 60)
    print("[RESULT] Structured JSON:")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Save JSON
    out_path = OUTPUT_DIR / (pdf_path.stem + ".json")
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[SAVED] {out_path}")


if __name__ == "__main__":
    main()
