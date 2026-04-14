import time
from crawler import crawl_github, crawl_portfolio, crawl_linkedin
from schema import Agent2Output, SocialProfileData, SummaryMetrics

def run_agent_2(agent_1_output):
    """Bộ não điều phối chính của Agent 2"""
    start_time = time.time()
    extracted_links = agent_1_output.get("extracted_links", [])

    profiles_data = []
    success_count = 0
    fail_count = 0

    for link_info in extracted_links:
        platform = link_info.get("platform", "").lower()
        url = link_info.get("url", "")
        print(f"[*] Đang xử lý: {platform} - {url}")

        if platform == "github":
            result = crawl_github(url)
        elif platform == "linkedin":
            result = crawl_linkedin(url)
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

    validated_output = Agent2Output(
        candidate_id=agent_1_output.get("candidate_id", "unknown"),
        social_profiles_data=profiles_data,
        summary_metrics=SummaryMetrics(
            total_links_received=len(extracted_links),
            successful_crawls=success_count,
            failed_crawls=fail_count
        ),
        execution_time_ms=execution_time_ms
    )

    return validated_output.model_dump()