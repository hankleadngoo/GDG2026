"""
verifier.py — Agent 3: Verifier Agent
=====================================

One public function:

    run_agent3(state)  →  dict
        Cross-checks CV data against OSINT data and updates the state with
        verification results.

Environment variables (loaded from .env):
    GOOGLE_API_KEY   — Gemini API key
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .schema import Agent3Output

# ── Bootstrap ─────────────────────────────────────────────────────────────────

load_dotenv()

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

VERIFIER_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 5

# ── Google GenAI client ───────────────────────────────────────────────────────

def _get_genai_client() -> genai.Client:
    api_key = os.environ["GOOGLE_API_KEY"]
    return genai.Client(api_key=api_key)


# ── Prompt Templates ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
Bạn là một chuyên gia thẩm định hồ sơ năng lực.
Nhiệm vụ của bạn là so sánh thông tin từ CV (Dữ liệu Agent 1) với dữ liệu thực tế từ internet (Dữ liệu Agent 2).

Quy tắc thẩm định (Trạng thái - Status):
1. VERIFIED: Thông tin khớp nhau hoặc bổ trợ cho nhau.
2. WARNING: Có sự sai lệch nhỏ về thời gian, thuật ngữ hoặc dữ liệu không hoàn toàn chắc chắn.
3. INCONSISTENT: CV ghi một đằng, dữ liệu thực tế chứng minh một nẻo (VD: CV ghi thạo Java nhưng Github chỉ có Python).
4. NO_EVIDENCE: Không tìm thấy bất kỳ dấu vết nào để kiểm chứng trên internet.

Hãy đưa ra điểm tin cậy (overall_trust_score) từ 0-100 dựa trên mức độ trung thực của hồ sơ.
TRẢ VỀ ĐÚNG ĐỊNH DẠNG JSON. Không bao gồm các ký tự markdown (```json).
"""

_VERIFICATION_PROMPT = """\
Hãy thực hiện đối soát và trả về báo cáo thẩm định:

{{
  "overall_trust_score": <float 0-100>,
  "verification_details": [
    {{
      "category": "<Skills | Experience | Education | ...>",
      "claim": "<thông tin trên CV>",
      "evidence": "<thông tin tìm thấy trên mạng>",
      "status": "<VERIFIED | WARNING | INCONSISTENT | NO_EVIDENCE>",
      "reasoning": "<lý do kết luận>"
    }}
  ],
  "red_flags": ["<cảnh báo nghiêm trọng 1>", "<cảnh báo nghiêm trọng 2>"],
  "summary_report": "<tổng kết ngắn gọn về độ trung thực>"
}}

--- DỮ LIỆU CV (AGENT 1) ---
{agent1_data}

--- DỮ LIỆU OSINT (AGENT 2) ---
{agent2_data}
"""

# ── Extraction Helper ─────────────────────────────────────────────────────────

def _generate_verification_report(
    agent1_data: dict,
    agent2_data: dict,
    candidate_id: str
) -> Agent3Output | None:
    """
    Call Gemini Flash to cross-reference data.
    Implements exponential backoff with jitter for rate limits (429/503).
    """
    client = _get_genai_client()
    
    a1_str = json.dumps(agent1_data, ensure_ascii=False)
    a2_str = json.dumps(agent2_data, ensure_ascii=False)
    
    user_prompt = _VERIFICATION_PROMPT.format(
        agent1_data=a1_str,
        agent2_data=a2_str
    )

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=VERIFIER_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.0, # Cần tính chính xác tuyệt đối, không sáng tạo
                ),
            )
            
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            
            data = json.loads(raw)
            data["candidate_id"] = candidate_id
            return Agent3Output.from_dict(data)

        except Exception as exc:
            error_msg = str(exc)
            if ("503" in error_msg or "429" in error_msg) and attempt < MAX_RETRIES - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1) # Exponential backoff + Jitter
                logger.warning("Agent 3: Server bận (503/429). Thử lại lần %d sau %.2fs...", attempt + 1, wait_time)
                time.sleep(wait_time)
            elif type(exc) == json.JSONDecodeError and attempt < MAX_RETRIES - 1:
                logger.warning("Agent 3: Lỗi parse JSON. Thử lại lần %d...", attempt + 1)
                time.sleep(1)
            else:
                logger.error("Agent 3 thất bại sau %d lần thử: %s", MAX_RETRIES, error_msg)
                return None
                
    return None


# ── Public function: Verify ───────────────────────────────────────────────────

def run_agent3(state: dict[str, Any]) -> dict[str, Any]:
    """
    Cross-reference candidate CV against OSINT data to generate a Trust Score.

    Reads from state:
        state["candidate_id"]
        state["agent1_output"]
        state["agent2_output"]
        state["pipeline_warnings"]

    Writes to state (and returns the updated state dict):
        state["agent3_output"]
    """
    warnings: list[str] = state.setdefault("pipeline_warnings", [])
    
    candidate_id: str = state.get("candidate_id", "unknown_id")
    agent1_data: dict = state.get("agent1_output", {})
    agent2_data: dict = state.get("agent2_output", {})

    if not agent1_data or not agent2_data:
        msg = "agent3: skipped verification — missing input from Agent 1 or Agent 2"
        warnings.append(msg)
        logger.warning(msg)
        state["agent3_output"] = None
        return state

    logger.info("Agent 3 starting cross-verification for candidate %s...", candidate_id)
    
    verification_payload = _generate_verification_report(
        agent1_data=agent1_data,
        agent2_data=agent2_data,
        candidate_id=candidate_id
    )

    if verification_payload is None:
        warnings.append("agent3: verification failed — API error or malformed JSON")
        state["agent3_output"] = None
    else:
        state["agent3_output"] = verification_payload.to_dict()
        logger.info(
            "Agent 3 finished. Trust Score: %.1f | Red Flags: %d", 
            verification_payload.overall_trust_score,
            len(verification_payload.red_flags)
        )

    return state