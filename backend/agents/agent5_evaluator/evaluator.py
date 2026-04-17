"""
evaluator.py — Agent 5: Final Evaluator
=======================================

One public function:

    run_agent5(state)  →  dict
        Aggregates outputs from Agents 1, 3, and 4 to generate the final
        recruitment decision and HR reports.

Environment variables (loaded from .env):
    GOOGLE_API_KEY   — Gemini API key
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

from .schema import Agent5Output

# ── Bootstrap ─────────────────────────────────────────────────────────────────

load_dotenv()

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

EVALUATION_MODEL = "gemini-1.5-pro"
MAX_RETRIES = 3

# ── Google GenAI client ───────────────────────────────────────────────────────

def _get_genai_client() -> genai.Client:
    api_key = os.environ["GOOGLE_API_KEY"]
    return genai.Client(api_key=api_key)


# ── Prompt Templates ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
Bạn là Giám đốc Nhân sự (HR Director) và Chuyên gia Đánh giá Năng lực cấp cao.
Nhiệm vụ của bạn là tổng hợp toàn bộ dữ liệu từ các Agent trước đó để đưa ra quyết định tuyển dụng cuối cùng.

HƯỚNG DẪN SUY LUẬN:
1. Đặt 'Tính trung thực' (Dữ liệu Agent 3) lên hàng đầu. Nếu có cờ đỏ nghiêm trọng, hãy cân nhắc REJECT.
2. Dữ liệu Agent 4 (Mặt bằng chung) chỉ là tham khảo. Đừng loại ứng viên chỉ vì số năm kinh nghiệm thấp nếu họ có dự án OSINT thực tế tốt.
3. Chủ động suy luận điểm mạnh/yếu mà CV không viết thẳng ra.
4. hr_internal_notes phải sắc bén, cảnh báo rủi ro cho HR.
5. candidate_feedback_email phải chuyên nghiệp, mang tính xây dựng.

Trả về ONLY một đối tượng JSON hợp lệ tuân thủ đúng các key được yêu cầu. Không thêm markdown hay text bên ngoài.
"""

_EVALUATION_PROMPT = """\
Hãy phân tích chuyên sâu các dữ liệu sau và trả về JSON:

{{
  "overall_evaluation": {{
    "score": <int 0-100>,
    "reasoning": "<lý do>"
  }},
  "inferred_strengths": ["<điểm mạnh 1>", "<điểm mạnh 2>"],
  "inferred_weaknesses": ["<điểm yếu 1>", "<điểm yếu 2>"],
  "market_comparison_notes": "<nhận xét so với mặt bằng chung>",
  "final_decision": "<HIRE | INTERVIEW_HIGH_PRIORITY | INTERVIEW_STANDARD | REJECT | NEED_MORE_INFO>",
  "hr_internal_notes": "<lưu ý nội bộ>",
  "candidate_feedback_email": "<nội dung email nháp>"
}}

--- DỮ LIỆU CV (AGENT 1) ---
{agent1_data}

--- BÁO CÁO THẨM ĐỊNH (AGENT 3) ---
{agent3_data}

--- MẶT BẰNG CHUNG (AGENT 4) ---
{agent4_data}
"""

# ── Payload extraction helper ─────────────────────────────────────────────────

def _generate_evaluation(
    agent1_data: dict,
    agent3_data: dict,
    agent4_data: dict,
    candidate_id: str
) -> Agent5Output | None:
    """
    Call Gemini Pro to evaluate the candidate. 
    Returns None on failure.
    """
    try:
        client = _get_genai_client()
        
        # Serialize dicts to string for prompt
        a1_str = json.dumps(agent1_data, ensure_ascii=False)
        a3_str = json.dumps(agent3_data, ensure_ascii=False)
        a4_str = json.dumps(agent4_data, ensure_ascii=False)
        
        user_prompt = _EVALUATION_PROMPT.format(
            agent1_data=a1_str,
            agent3_data=a3_str,
            agent4_data=a4_str
        )

        for attempt in range(MAX_RETRIES):
            try:
                response = client.models.generate_content(
                    model=EVALUATION_MODEL,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.2, # Low temperature for logical consistency
                    ),
                )
                
                raw = response.text.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                
                data = json.loads(raw)
                data["candidate_id"] = candidate_id
                return Agent5Output.from_dict(data)
                
            except json.JSONDecodeError as exc:
                logger.warning("Agent 5: JSON parsing failed on attempt %d: %s", attempt + 1, exc)
                time.sleep(2 ** attempt)
            except Exception as exc:
                logger.warning("Agent 5: API call failed on attempt %d: %s", attempt + 1, exc)
                time.sleep(2 ** attempt)
                
        return None
    except Exception as exc:
        logger.error("Agent 5: Critical error in _generate_evaluation: %s", exc)
        return None


# ── Public function 1: Evaluate ───────────────────────────────────────────────

def run_agent5(state: dict[str, Any]) -> dict[str, Any]:
    """
    Consume data from previous agents and generate the final HR evaluation.

    Reads from state:
        state["candidate_id"]
        state["agent1_output"]     — parsed CV data
        state["agent3_output"]     — verification & trust score
        state["benchmark"]         — agent 4 market comparison
        state["pipeline_warnings"]

    Writes to state (and returns the updated state dict):
        state["final_evaluation"]  — dict payload of Agent5Output
    """
    warnings: list[str] = state.setdefault("pipeline_warnings", [])
    
    candidate_id: str = state.get("candidate_id", "unknown_id")
    agent1_data: dict = state.get("agent1_output", {})
    agent3_data: dict = state.get("agent3_output", {})
    agent4_data: dict = state.get("benchmark", {})

    # Edge case: Missing core data
    if not agent1_data or not agent3_data:
        msg = "agent5: skipped evaluation — missing critical input from Agent 1 or 3"
        warnings.append(msg)
        logger.warning(msg)
        state["final_evaluation"] = None
        return state

    # 1. Generate Evaluation
    logger.info("Agent 5 processing evaluation for candidate %s...", candidate_id)
    evaluation_payload = _generate_evaluation(
        agent1_data=agent1_data,
        agent3_data=agent3_data,
        agent4_data=agent4_data,
        candidate_id=candidate_id
    )

    # 2. Handle output
    if evaluation_payload is None:
        warnings.append("agent5: evaluation failed — Gemini extraction or validation error")
        state["final_evaluation"] = None
    else:
        state["final_evaluation"] = evaluation_payload.to_dict()
        logger.info(
            "Agent 5 finished. Decision: %s | Score: %d", 
            evaluation_payload.final_decision, 
            evaluation_payload.overall_evaluation.score
        )

    return state