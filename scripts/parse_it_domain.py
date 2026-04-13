"""
scripts/parse_it_domain.py
--------------------------
Batch-parse all PDFs in data/it-domain/ into Markdown files using LlamaParse.
Output is saved to data/it-domain-md/<original_stem>.md

Usage (from repo root, with venv activated):
    python scripts/parse_it_domain.py

Requirements:
    pip install llama-parse python-dotenv tqdm

Environment variables (in .env):
    LLAMA_CLOUD_API_KEY=<your key from cloud.llamaindex.ai>
"""

import os
import sys
import json
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
load_dotenv()

REPO_ROOT   = Path(__file__).parent.parent
INPUT_DIR   = REPO_ROOT / "data" / "it-domain"
OUTPUT_DIR  = REPO_ROOT / "data" / "it-domain-md"
LOG_FILE    = REPO_ROOT / "data" / "it-domain-md" / "_parse_log.json"

LLAMA_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
if not LLAMA_API_KEY:
    sys.exit("❌  LLAMA_CLOUD_API_KEY not set in .env — get your key at https://cloud.llamaindex.ai")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_pending_pdfs() -> list[Path]:
    """Return PDFs that have not yet been parsed (no corresponding .md file)."""
    all_pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    pending = [
        p for p in all_pdfs
        if not (OUTPUT_DIR / (p.stem + ".md")).exists()
    ]
    return pending


def save_markdown(pdf_path: Path, markdown: str) -> Path:
    out_path = OUTPUT_DIR / (pdf_path.stem + ".md")
    out_path.write_text(markdown, encoding="utf-8")
    return out_path


def load_log() -> dict:
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    return {"success": [], "failed": [], "skipped": []}


def save_log(log: dict) -> None:
    LOG_FILE.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Core parsing — one file at a time (safe for free-tier rate limits)
# ---------------------------------------------------------------------------

async def parse_one(pdf_path: Path, parser) -> str:
    """Parse a single PDF and return markdown string."""
    documents = await parser.aload_data(str(pdf_path))
    # LlamaParse returns a list of Document objects; join all pages
    return "\n\n".join(doc.text for doc in documents if doc.text.strip())


async def run_batch(pdfs: list[Path], log: dict) -> None:
    from llama_parse import LlamaParse  # import here so missing dep gives a clear error

    parser = LlamaParse(
        api_key=LLAMA_API_KEY,
        result_type="markdown",
        verbose=False,
        language="en",
    )

    print(f"\n📄  Parsing {len(pdfs)} PDFs → {OUTPUT_DIR}\n")

    for pdf_path in tqdm(pdfs, unit="file", ncols=80):
        try:
            markdown = await parse_one(pdf_path, parser)

            if len(markdown.strip()) < 50:
                # Likely a scanned image-only PDF — record but save empty stub
                tqdm.write(f"  ⚠  Short output ({len(markdown)} chars): {pdf_path.name}")
                log["skipped"].append({"file": pdf_path.name, "reason": "short_output"})
                save_markdown(pdf_path, f"<!-- parse_skipped: short output -->\n{markdown}")
            else:
                save_markdown(pdf_path, markdown)
                log["success"].append(pdf_path.name)

        except Exception as exc:
            tqdm.write(f"  ❌  Failed: {pdf_path.name} — {exc}")
            log["failed"].append({"file": pdf_path.name, "error": str(exc)})

        # Save log after every file so progress survives interruption
        save_log(log)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    log = load_log()

    all_pdfs  = sorted(INPUT_DIR.glob("*.pdf"))
    pending   = get_pending_pdfs()
    already   = len(all_pdfs) - len(pending)

    print(f"📁  Input  : {INPUT_DIR}  ({len(all_pdfs)} PDFs total)")
    print(f"📁  Output : {OUTPUT_DIR}")
    print(f"✅  Already parsed : {already}")
    print(f"⏳  Pending        : {len(pending)}")

    if not pending:
        print("\n🎉  All PDFs already parsed. Nothing to do.")
        print(f"    Success: {len(log['success'])}  |  Skipped: {len(log['skipped'])}  |  Failed: {len(log['failed'])}")
        return

    asyncio.run(run_batch(pending, log))

    print("\n─── Summary ───────────────────────────────────────")
    print(f"  ✅  Success : {len(log['success'])}")
    print(f"  ⚠   Skipped : {len(log['skipped'])}  (short / image-only)")
    print(f"  ❌  Failed  : {len(log['failed'])}")
    print(f"  📋  Log     : {LOG_FILE}")
    print("────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
