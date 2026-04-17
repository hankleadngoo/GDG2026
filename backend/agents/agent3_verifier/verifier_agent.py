import json
import os
import time
import random
import logging

logger = logging.getLogger(__name__)

def run_agent_3(agent1_output, agent2_output, model="gemini-2.5-flash"):
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    user_prompt = f"""
    DỮ LIỆU CV (AGENT 1):
    {json.dumps(agent1_output, ensure_ascii=False)}

    DỮ LIỆU OSINT (AGENT 2):
    {json.dumps(agent2_output, ensure_ascii=False)}

    Hãy thực hiện đối soát và trả về báo cáo thẩm định dưới dạng JSON.
    """

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction="Bạn là chuyên gia thẩm định hồ sơ. So khớp CV và OSINT để tìm sai sót hoặc xác thực năng lực.", # Prompt hệ thống của Agent 3
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
            return json.loads(response.text)
            
        except Exception as e:
            error_msg = str(e)
            # Nếu gặp lỗi 503 (quá tải) hoặc 429 (hết quota)
            if ("503" in error_msg or "429" in error_msg) and attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ Agent 3: Server bận. Đang thử lại lần {attempt + 1} sau {wait_time:.2f}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Agent 3 thất bại sau {max_retries} lần thử: {e}")
                return {"status": "error", "message": error_msg}