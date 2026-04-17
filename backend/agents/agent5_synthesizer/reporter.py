import json
import os
import time
import logging
from google import genai
from google.genai import types

from backend.agents.agent5_evaluator.prompt import SYSTEM_PROMPT
from backend.agents.agent5_evaluator.schema import Agent5Output

logger = logging.getLogger(__name__)

def run_agent_5(agent1_output: dict, agent3_output: dict, agent4_output: dict, model="gemini-1.5-pro") -> dict:
    """
    Agent 5: Quyết định tổng hợp và Đánh giá ứng viên.
    Sử dụng mô hình Pro để đảm bảo khả năng suy luận logic sâu.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    candidate_id = agent1_output.get("candidate_id", "unknown_id")

    user_prompt = f"""
    --- DỮ LIỆU ỨNG VIÊN (AGENT 1) ---
    {json.dumps(agent1_output, ensure_ascii=False)}

    --- BÁO CÁO THẨM ĐỊNH (AGENT 3) ---
    {json.dumps(agent3_output, ensure_ascii=False)}

    --- MẶT BẰNG CHUNG NGÀNH (AGENT 4) ---
    {json.dumps(agent4_output, ensure_ascii=False)}

    Hãy phân tích chuyên sâu và trả về JSON chuẩn theo đúng Schema đã định.
    Candidate ID: {candidate_id}
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2, # Cần tính logic và ổn định cao
                    response_schema=Agent5Output # Ép trả về đúng schema Pydantic
                ),
            )
            
            # Trả về dict đã được parse
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"Agent 5 Error (Attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return {
                    "candidate_id": candidate_id,
                    "status": "error",
                    "message": "Không thể tạo đánh giá tổng hợp từ AI sau nhiều lần thử."
                }

# Ví dụ chạy test
if __name__ == "__main__":
    # Mock data để test nhanh
    dummy_a1 = {"candidate_id": "C123", "name": "Nguyễn Văn A", "skills": ["Python", "React"]}
    dummy_a3 = {"trust_score": 85, "verification": "VERIFIED"}
    dummy_a4 = {"pool_size": 100, "candidate_exp_percentile": 0.75}
    
    print(json.dumps(run_agent_5(dummy_a1, dummy_a3, dummy_a4), ensure_ascii=False, indent=2))