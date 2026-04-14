from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GithubProfileInfo(BaseModel):
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    account_created_at: Optional[str] = None

class GithubMetrics(BaseModel):
    followers: int = 0
    public_repos: int = 0
    total_stars_received: int = 0

class GithubTechStack(BaseModel):
    primary_languages: List[str] = Field(default_factory=list)
    last_active: Optional[str] = None

class GithubRepo(BaseModel):
    name: str
    description: Optional[str] = ""
    primary_language: str = "Unknown"
    stars: int = 0
    url: str

class GithubRichData(BaseModel):
    profile_info: GithubProfileInfo
    metrics: GithubMetrics
    tech_stack_analysis: GithubTechStack
    top_highlighted_repos: List[GithubRepo]

class SocialProfileData(BaseModel):
    platform: str
    original_url: str
    crawl_status: str
    error_message: Optional[str] = None
    raw_cleaned_data: Optional[Dict[str, Any]] = None

class SummaryMetrics(BaseModel):
    total_links_received: int = 0
    successful_crawls: int = 0
    failed_crawls: int = 0

class Agent2Output(BaseModel):
    candidate_id: str
    agent_2_status: str = "completed"
    social_profiles_data: List[SocialProfileData]
    summary_metrics: SummaryMetrics
    execution_time_ms: int