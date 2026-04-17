"""
schema.py — Structured data schema for Agent 2 (OSINT).

Defines the dataclasses for parsed GitHub data, portfolio data, and the
final Agent 2 output payload.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# ── Sub-Schemas for GitHub ────────────────────────────────────────────────────

@dataclass
class GithubProfileInfo:
    bio: str | None = None
    company: str | None = None
    location: str | None = None
    account_created_at: str | None = None

@dataclass
class GithubMetrics:
    followers: int = 0
    public_repos: int = 0
    total_stars_received: int = 0

@dataclass
class GithubTechStack:
    primary_languages: list[str] = field(default_factory=list)
    last_active: str | None = None

@dataclass
class GithubRepo:
    name: str
    url: str
    description: str = ""
    primary_language: str = "Unknown"
    stars: int = 0
    readme_content: str | None = None

@dataclass
class CandidateExpertise:
    project_summaries: list[dict[str, str]]
    strength_analysis: str
    focus_area: str

@dataclass
class GithubRichData:
    profile_info: GithubProfileInfo
    metrics: GithubMetrics
    tech_stack_analysis: GithubTechStack
    top_highlighted_repos: list[GithubRepo]
    ai_expertise_analysis: dict | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

# ── Sub-Schemas for General Profiles ──────────────────────────────────────────

@dataclass
class SocialProfileData:
    platform: str
    original_url: str
    crawl_status: str
    error_message: str | None = None
    raw_cleaned_data: dict[str, Any] | None = None

@dataclass
class SummaryMetrics:
    total_links_received: int = 0
    successful_crawls: int = 0
    failed_crawls: int = 0

# ── Main Agent 2 Output Schema ────────────────────────────────────────────────

@dataclass
class Agent2Output:
    candidate_id: str
    agent_2_status: str
    social_profiles_data: list[SocialProfileData]
    summary_metrics: SummaryMetrics
    execution_time_ms: int

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for pipeline state storage."""
        return asdict(self)