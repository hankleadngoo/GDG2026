import requests
import re
import os
import base64
from bs4 import BeautifulSoup
from backend.agents.agent2_osint.schema import (
    GithubRichData, GithubProfileInfo, GithubMetrics, 
    GithubTechStack, GithubRepo
)

def normalize_github_url(url):
    url = url.strip().lower()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def crawl_github(url):
    url = normalize_github_url(url)
    match = re.search(r'github\.com/([^/]+)', url)
    if not match:
        return {"status": "failed_invalid_url", "error": "Invalid URL", "data": None}

    username = match.group(1).split('/')[0]
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    
    try:
        # 1. Lấy thông tin Profile
        u_res = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=10)
        if u_res.status_code != 200:
            return {"status": "failed_api", "error": f"Status {u_res.status_code}", "data": None}
        user_data = u_res.json()

        # 2. Lấy Repos và README
        r_res = requests.get(f"https://api.github.com/users/{username}/repos?per_page=10&sort=updated", headers=headers, timeout=10)
        repos_data = r_res.json() if r_res.status_code == 200 else []

        repo_list = []
        languages_dict = {}
        total_stars = 0

        for repo in repos_data:
            if repo.get("fork"): continue
            
            name = repo.get("name")
            stars = repo.get("stargazers_count", 0)
            total_stars += stars
            lang = repo.get("language")
            if lang: languages_dict[lang] = languages_dict.get(lang, 0) + 1

            # Lấy README để hiểu nội dung nghiên cứu
            readme_text = ""
            readme_res = requests.get(f"https://api.github.com/repos/{username}/{name}/readme", headers=headers, timeout=5)
            if readme_res.status_code == 200:
                try:
                    content_b64 = readme_res.json().get("content", "")
                    readme_text = base64.b64decode(content_b64).decode('utf-8', errors='ignore')[:1500]
                except: pass

            repo_list.append({
                "name": name,
                "description": repo.get("description") or "",
                "primary_language": lang or "Unknown",
                "stars": stars,
                "url": repo.get("html_url"),
                "readme_content": readme_text
            })

        top_repos = sorted(repo_list, key=lambda x: x["stars"], reverse=True)[:5]

        rich_data = GithubRichData(
            profile_info=GithubProfileInfo(
                bio=user_data.get("bio") or "",
                company=user_data.get("company") or "",
                location=user_data.get("location") or "",
                account_created_at=user_data.get("created_at")
            ),
            metrics=GithubMetrics(
                followers=user_data.get("followers", 0),
                public_repos=user_data.get("public_repos", 0),
                total_stars_received=total_stars
            ),
            tech_stack_analysis=GithubTechStack(
                primary_languages=sorted(languages_dict, key=languages_dict.get, reverse=True)[:3],
                last_active=user_data.get("updated_at")
            ),
            top_highlighted_repos=[GithubRepo(**r) for r in top_repos]
        )
        return {"status": "success", "error": None, "data": rich_data.model_dump()}

    except Exception as e:
        return {"status": "error", "error": str(e), "data": None}

# Giữ nguyên crawl_portfolio và crawl_linkedin như bạn đã cung cấp
def crawl_portfolio(url):
    """Cào và làm sạch văn bản từ một trang web bất kỳ (Portfolio)."""
    import re
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        # Loại bỏ các thành phần không cần thiết
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()

        raw_text = soup.get_text(separator=' ', strip=True)
        cleaned_text = re.sub(r'\s+', ' ', raw_text)[:3000]

        return {"status": "success", "error": None, "data": {"website_content": cleaned_text}}
    except Exception as e:
        return {"status": "failed_network_error", "error": str(e), "data": None}
    
def crawl_linkedin(url):
    """
    LinkedIn yêu cầu cơ chế đăng nhập và Proxy phức tạp.
    Hiện tại hàm này trả về trạng thái skipped để không làm gián đoạn pipeline.
    """
    return {
        "status": "skipped", 
        "error": "LinkedIn crawling is currently disabled to avoid bot detection.", 
        "data": None
    }