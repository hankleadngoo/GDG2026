import requests
import re
from bs4 import BeautifulSoup

# Chỉ đường dẫn rõ ràng vào schema
from agents.agent2_osint.schema import (
    GithubRichData, GithubProfileInfo, GithubMetrics, 
    GithubTechStack, GithubRepo
)

# ... (Phần code bên dưới giữ nguyên) ...

def crawl_github(url):
    """Trích xuất dữ liệu CHUYÊN SÂU từ GitHub Profile bằng API."""
    match = re.search(r'github\.com/([^/]+)', url)
    if not match:
        return {"status": "failed_invalid_url", "error": "Không trích xuất được username", "data": None}

    username = match.group(1)
    user_api_url = f"https://api.github.com/users/{username}"
    repos_api_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed"

    try:
        user_response = requests.get(user_api_url, timeout=10)
        if user_response.status_code == 404:
            return {"status": "failed_404", "error": "Không tìm thấy GitHub profile", "data": None}
        elif user_response.status_code == 403:
            return {"status": "failed_rate_limit", "error": "Bị giới hạn API", "data": None}

        user_data = user_response.json()
        repos_response = requests.get(repos_api_url, timeout=10)
        repos_data = repos_response.json() if repos_response.status_code == 200 else []

        total_stars = 0
        languages_set = set()
        repo_list = []

        for repo in repos_data:
            if not repo.get("fork"): 
                total_stars += repo.get("stargazers_count", 0)
                if repo.get("language"):
                    languages_set.add(repo.get("language"))

                repo_list.append({
                    "name": repo.get("name"),
                    "description": repo.get("description", ""),
                    "primary_language": repo.get("language", "Unknown"),
                    "stars": repo.get("stargazers_count", 0),
                    "url": repo.get("html_url")
                })

        top_repos = sorted(repo_list, key=lambda x: x["stars"], reverse=True)[:3]

        rich_data = GithubRichData(
            profile_info=GithubProfileInfo(
                bio=user_data.get("bio"),
                company=user_data.get("company"),
                location=user_data.get("location"),
                account_created_at=user_data.get("created_at")
            ),
            metrics=GithubMetrics(
                followers=user_data.get("followers", 0),
                public_repos=user_data.get("public_repos", 0),
                total_stars_received=total_stars
            ),
            tech_stack_analysis=GithubTechStack(
                primary_languages=list(languages_set)[:10],
                last_active=user_data.get("updated_at")
            ),
            top_highlighted_repos=[GithubRepo(**r) for r in top_repos]
        )

        return {"status": "success", "error": None, "data": rich_data.model_dump()}

    except Exception as e:
        return {"status": "failed_system_error", "error": str(e), "data": None}

def crawl_portfolio(url):
    """Cào và làm sạch văn bản từ một trang web bất kỳ."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 404:
            return {"status": "failed_404", "error": "HTTP 404 - Không tìm thấy trang", "data": None}
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()

        raw_text = soup.get_text(separator=' ', strip=True)
        cleaned_text = re.sub(r'\s+', ' ', raw_text)[:3000]

        return {"status": "success", "error": None, "data": {"website_content": cleaned_text}}
    except Exception as e:
        return {"status": "failed_network_error", "error": str(e), "data": None}

def crawl_linkedin(url):
    """Mock dữ liệu LinkedIn MVP"""
    return {"status": "failed_private_profile", "error": "LinkedIn yêu cầu đăng nhập", "data": None}