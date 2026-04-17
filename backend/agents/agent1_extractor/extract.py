"""
extract_data.py — Batch processing script for Agent 1 (CV Extractor)
====================================================================
Executes concurrent CV parsing on a directory of PDF/DOCX files.
Aggregates the extracted JSONs into a single talent pool database.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from tqdm.asyncio import tqdm

from backend.agents.agent1_extractor.parser import parse_cv

# ── Bootstrap ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline_error.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── Core Processing ───────────────────────────────────────────────────────────

async def process_single_cv(file_path: Path, output_folder: Path) -> dict[str, Any] | None:
    """Process a single CV and save its JSON output. Skip if already exists."""
    output_file = output_folder / f"{file_path.stem}.json"
    if output_file.exists():
        return None

    try:
        loop = asyncio.get_event_loop()
        # parse_cv is synchronous, run in executor to avoid blocking event loop
        result = await loop.run_in_executor(None, parse_cv, str(file_path))
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    except Exception as e:
        logger.error("Failed to process %s: %s", file_path.name, str(e))
        return {"file": file_path.name, "error": str(e)}

async def main_pipeline(input_dir: str, output_json_file: str, max_workers: int = 10) -> None:
    """Scan directory, process CVs concurrently, and aggregate results."""
    input_path = Path(input_dir)
    output_final = Path(output_json_file)
    
    temp_output = input_path / "extracted_temp"
    temp_output.mkdir(exist_ok=True)
    
    extensions = {".pdf", ".docx"}
    cv_files = [f for f in input_path.iterdir() if f.suffix.lower() in extensions]
    
    print(f"--- Bắt đầu xử lý {len(cv_files)} CVs với {max_workers} workers ---")

    semaphore = asyncio.Semaphore(max_workers)

    async def sem_task(file: Path) -> dict[str, Any] | None:
        async with semaphore:
            return await process_single_cv(file, temp_output)

    tasks = [sem_task(f) for f in cv_files]
    await tqdm.gather(*tasks, desc="Đang trích xuất CV")

    print("\n--- Đang gộp dữ liệu thành file cuối cùng ---")
    all_results = []
    for json_file in temp_output.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            all_results.append(json.load(f))

    with open(output_final, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"Hoàn thành! Dữ liệu đã lưu tại: {output_final}")

# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    INPUT_FOLDER = "E:/GDG/data/it-domain"  
    OUTPUT_FILE = "E:/GDG/data/it_domain_extracted_cv_database.json"
    CONCURRENT_REQUESTS = 15
    
    asyncio.run(main_pipeline(INPUT_FOLDER, OUTPUT_FILE, CONCURRENT_REQUESTS))