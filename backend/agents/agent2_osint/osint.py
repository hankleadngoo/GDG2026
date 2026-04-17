"""
osint.py — Agent 2: OSINT Orchestrator
======================================

One public function:

    run_agent2(state)  →  dict
        Extracts target URLs from Agent 1, triggers the appropriate crawler,
        uses Gemini to analyze expertise (for GitHub), and updates the state.

Environment variables (loaded from .env):
    GOOGLE_API_KEY   — Gemini API key
    GITHUB_TOKEN     — Optional, for rate limits
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .crawler import crawl_github, crawl_linkedin, crawl_portfolio
from .schema import Agent2Output, SocialProfileData, SummaryMetrics

# ── Bootstrap ─────────────────────────────────────────────────────────────────

load_dotenv()

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

EXPERTISE_MODEL = "gemini-1.5-flash"
MAX_RETRIES = 3

# ── Google GenAI client ───────────────────────────────────────────────────────

def _get_genai_client() -> genai.Client:
    api_key = os.environ["GOOGLE_API_KEY"]
    return genai.Client(api_key=api_key)


# ── AI Analysis Helper ────────────────────────────────────────────────────────

_EXPERTISE_PROMPT = """\
Dựa trên dữ liệu GitHub của ứng viên dưới đây, hãy phân tích và trả về ONLY định dạng JSON hợp lệ:

{{
   "project_summaries": [{{ "name": "<tên>", "summary": "<tóm tắt ngắn gọn>" }}],
   "strength_analysis": "<nhận xét về kỹ năng và tư duy từ code/readme>",
   "focus_area": "<Software Engineering | AI Research | Mixed>"
}}

DỮ LIỆU GITHUB:
{repo_info}
"""

def _analyze_expertise_with_ai(github_data: dict) -> dict | None:
    """Sử dụng Gemini Flash để nhận xét chuyên môn từ README của GitHub."""
    repo_info = []
    for repo in github_data.get("top_highlighted_repos", []):
        repo_info.append({
            "name": repo.get('name'),
            "lang": repo.get('primary_language'),
            "readme": repo.get('readme_content', "No readme")[:800] if repo.get('readme_content') else "No readme"
        })

    if not repo_info:
        return None

    try:
        client = _get_genai_client()
        prompt = _EXPERTISE_PROMPT.format(repo_info=json.dumps(repo_info, ensure_ascii=False))
        
        response = client.models.generate_content(
            model=EXPERTISE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )
        
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
                
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Agent 2: Failed to analyze AI expertise: %s", exc)
        return None


# ── Public function: Run Agent 2 ──────────────────────────────────────────────

def run_agent2(state: dict[str, Any]) -> dict[str, Any]:
    """
    Run the OSINT pipeline based on URLs provided by Agent 1.

    Reads from state:
        state["candidate_id"]
        state["agent1_output"]["_osint_targets"]
        state["pipeline_warnings"]

    Writes to state (and returns the updated state dict):
        state["agent2_output"]
    """
    start_time = time.time()
    warnings: list[str] = state.setdefault("pipeline_warnings", [])
    
    candidate_id: str = state.get("candidate_id", "unknown_id")
    agent1_data: dict = state.get("agent1_output", {})
    
    # Extract links from Agent 1 (uses the hidden metadata field)
    extracted_links: list[dict] = agent1_data.get("_osint_targets", [])
    
    profiles_data: list[SocialProfileData] = []
    success_count = 0
    fail_count = 0

    if not extracted_links:
        msg = "agent2: no OSINT targets found in CV"
        warnings.append(msg)
        logger.info(msg)
    else:
        logger.info("Agent 2 starting OSINT for %d targets...", len(extracted_links))

    for link_info in extracted_links:
        platform = link_info.get("platform", "").lower()
        url = link_info.get("url", "")
        if not url: 
            continue
        
        logger.info("Agent 2 crawling: [%s] %s", platform, url)
        
        if platform == "github":
            result = crawl_github(url)
            # Fetch AI analysis if crawl succeeds
            if result["status"] == "success" and result["data"]:
                analysis = _analyze_expertise_with_ai(result["data"])
                result["data"]["ai_expertise_analysis"] = analysis
                
        elif platform == "linkedin":
            result = crawl_linkedin(url)
            
        else:
            result = crawl_portfolio(url)

        # Update metrics
        if result["status"] == "success":
            success_count += 1
        else:
            fail_count += 1

        # Append to profile data list
        profiles_data.append(SocialProfileData(
            platform=platform,
            original_url=url,
            crawl_status=result["status"],
            error_message=result.get("error"),
            raw_cleaned_data=result.get("data")
        ))

    execution_time_ms = int((time.time() - start_time) * 1000)

    # Compile the final payload
    output = Agent2Output(
        candidate_id=candidate_id,
        agent_2_status="completed",
        social_profiles_data=profiles_data,
        summary_metrics=SummaryMetrics(
            total_links_received=len(extracted_links),
            successful_crawls=success_count,
            failed_crawls=fail_count
        ),
        execution_time_ms=execution_time_ms
    )

    state["agent2_output"] = output.to_dict()
    
    logger.info("Agent 2 finished in %dms (Success: %d, Failed: %d)", 
                execution_time_ms, success_count, fail_count)
    
    return state