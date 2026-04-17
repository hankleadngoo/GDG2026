import time
import json
import os
from google import genai
from google.genai import types
from backend.agents.agent2_osint.crawler import crawl_github, crawl_portfolio
from backend.agents.agent2_osint.schema import Agent2Output, SocialProfileData, SummaryMetrics

def analyze_expertise_with_ai(github_data):
    """Sử dụng Gemini Flash để nhận xét chuyên môn từ README"""
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Chuẩn bị dữ liệu rút gọn để gửi lên AI
    repo_info = []
    for repo in github_data.get("top_highlighted_repos", []):
        repo_info.append({
            "name": repo['name'],
            "lang": repo['primary_language'],
            "readme": repo['readme_content'][:800] if repo.get('readme_content') else "No readme"
        })

    prompt = f"""
    Dựa trên dữ liệu GitHub của ứng viên: {json.dumps(repo_info, ensure_ascii=False)}
    Hãy thực hiện:
    1. Tóm tắt ngắn gọn từng dự án (tập trung vào giá trị nghiên cứu hoặc kỹ thuật).
    2. Nhận xét: Ứng viên thiên về Software Engineering (cấu trúc, công cụ) hay AI Research (thuật toán, mô hình)?
    3. Điểm mạnh nổi bật là gì?

    Trả về JSON:
    {{
       "project_summaries": [{{ "name": "tên", "summary": "tóm tắt" }}],
       "strength_analysis": "nhận xét...",
       "focus_area": "Software Engineering / AI Research / Mixed"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except:
        return None

def run_agent_2(agent_1_output):
    start_time = time.time()
    extracted_links = agent_1_output.get("_osint_targets", [])
    
    profiles_data = []
    success_count = 0
    fail_count = 0

    for link_info in extracted_links:
        platform = link_info.get("platform", "").lower()
        url = link_info.get("url", "")
        if not url: continue
        
        if platform == "github":
            result = crawl_github(url)
            # Nếu crawl thành công, gửi dữ liệu cho AI phân tích thế mạnh
            if result["status"] == "success" and result["data"]:
                analysis = analyze_expertise_with_ai(result["data"])
                result["data"]["ai_expertise_analysis"] = analysis
        elif platform == "linkedin":
            result = {"status": "skipped", "error": "LinkedIn disabled", "data": None}
        else:
            result = crawl_portfolio(url)

        if result["status"] == "success":
            success_count += 1
        else:
            fail_count += 1

        profiles_data.append(SocialProfileData(
            platform=platform,
            original_url=url,
            crawl_status=result["status"],
            error_message=result["error"],
            raw_cleaned_data=result["data"]
        ))

    execution_time_ms = int((time.time() - start_time) * 1000)

    return Agent2Output(
        candidate_id=agent_1_output.get("candidate_id", "unknown"),
        social_profiles_data=profiles_data,
        summary_metrics=SummaryMetrics(
            total_links_received=len(extracted_links),
            successful_crawls=success_count,
            failed_crawls=fail_count
        ),
        execution_time_ms=execution_time_ms
    ).model_dump()