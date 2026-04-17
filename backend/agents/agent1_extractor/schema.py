"""
schema.py — Structured data schema for Agent 1 (CV Extractor).

This is the canonical data contract between Agent 1 (Extractor) and the
downstream agents:
  - Agent 2 (OSINT): consumes `candidate`, `social_links`, `projects[].links`,
    `work_experience[].company_url` via `osint_targets()`
  - Agent 3 (Verifier): consumes the full object to cross-check OSINT results
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# ── Leaf Models ───────────────────────────────────────────────────────────────

@dataclass
class CandidateInfo:
    full_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None

@dataclass
class SocialLinks:
    linkedin: str | None = None
    github: str | None = None
    facebook: str | None = None
    portfolio: str | None = None
    other: list[str] = field(default_factory=list)

@dataclass
class Education:
    institution: str
    degree: str | None = None
    major: str | None = None
    gpa: str | None = None
    start_year: int | None = None
    end_year: int | None = None

@dataclass
class ProjectLinks:
    github: str | None = None
    demo: str | None = None
    other: list[str] = field(default_factory=list)

@dataclass
class Project:
    name: str
    description: str | None = None
    tech_stack: list[str] = field(default_factory=list)
    links: ProjectLinks = field(default_factory=ProjectLinks)
    role: str | None = None

@dataclass
class WorkExperience:
    company: str
    role: str
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    responsibilities: list[str] = field(default_factory=list)
    company_url: str | None = None

@dataclass
class Skills:
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)

@dataclass
class Certification:
    name: str
    issuer: str | None = None
    year: int | None = None
    url: str | None = None

@dataclass
class LanguageSpoken:
    language: str
    proficiency: str | None = None

@dataclass
class ExtractionMetadata:
    source_file: str
    parse_method: str
    extraction_model: str = "gemini-1.5-pro"
    extracted_at: str = ""
    warnings: list[str] = field(default_factory=list)

# ── Root Model ────────────────────────────────────────────────────────────────

@dataclass
class CVExtraction:
    """
    Top-level output of Agent 1. Passed verbatim to Agent 2 and Agent 3.
    """
    candidate: CandidateInfo
    metadata: ExtractionMetadata
    social_links: SocialLinks = field(default_factory=SocialLinks)
    education: list[Education] = field(default_factory=list)
    work_experience: list[WorkExperience] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    skills: Skills = field(default_factory=Skills)
    certifications: list[Certification] = field(default_factory=list)
    languages_spoken: list[LanguageSpoken] = field(default_factory=list)

    # ── Serialisation & Deserialisation ───────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CVExtraction":
        """
        Construct from a plain dict (e.g., parsed JSON from Gemini).
        Handles nested object instantiation explicitly since dataclasses
        do not auto-parse nested dicts by default.
        """
        candidate_data = data.get("candidate", {})
        candidate = CandidateInfo(**candidate_data) if isinstance(candidate_data, dict) else CandidateInfo(full_name="Unknown")

        meta_data = data.get("metadata", {})
        metadata = ExtractionMetadata(**meta_data) if isinstance(meta_data, dict) else ExtractionMetadata(source_file="unknown", parse_method="unknown")

        social_data = data.get("social_links", {})
        social_links = SocialLinks(**social_data) if isinstance(social_data, dict) else SocialLinks()

        skills_data = data.get("skills", {})
        skills = Skills(**skills_data) if isinstance(skills_data, dict) else Skills()

        education = [Education(**e) for e in data.get("education", []) if isinstance(e, dict)]
        certifications = [Certification(**c) for c in data.get("certifications", []) if isinstance(c, dict)]
        languages_spoken = [LanguageSpoken(**l) for l in data.get("languages_spoken", []) if isinstance(l, dict)]
        
        work_experience = [WorkExperience(**w) for w in data.get("work_experience", []) if isinstance(w, dict)]
        
        projects = []
        for p in data.get("projects", []):
            if isinstance(p, dict):
                links_data = p.pop("links", {})
                links = ProjectLinks(**links_data) if isinstance(links_data, dict) else ProjectLinks()
                projects.append(Project(links=links, **p))

        return cls(
            candidate=candidate,
            metadata=metadata,
            social_links=social_links,
            education=education,
            work_experience=work_experience,
            projects=projects,
            skills=skills,
            certifications=certifications,
            languages_spoken=languages_spoken
        )

    # ── Helpers for Downstream Agents ─────────────────────────────────────────

    def all_urls(self) -> list[str]:
        """Return every URL found anywhere in the extraction (for general indexing)."""
        urls: list[str] = []

        sl = self.social_links
        for attr in ("linkedin", "github", "facebook", "portfolio"):
            val = getattr(sl, attr)
            if val:
                urls.append(val)
        urls.extend(sl.other)

        for proj in self.projects:
            for attr in ("github", "demo"):
                val = getattr(proj.links, attr)
                if val:
                    urls.append(val)
            urls.extend(proj.links.other)

        for exp in self.work_experience:
            if exp.company_url:
                urls.append(exp.company_url)

        for cert in self.certifications:
            if cert.url:
                urls.append(cert.url)

        # Deduplicate and preserve order
        return list(dict.fromkeys(urls))

    def osint_targets(self) -> list[dict]:
        """
        Compact list of targets for Agent 2 to investigate.
        Returns a list of dicts with 'platform' and 'url'.
        """
        targets = []
        
        # Socials
        if self.social_links.github:
            targets.append({"platform": "github", "url": self.social_links.github})
        if self.social_links.linkedin:
            targets.append({"platform": "linkedin", "url": self.social_links.linkedin})
        if self.social_links.portfolio:
            targets.append({"platform": "portfolio", "url": self.social_links.portfolio})
        if self.social_links.facebook:
            targets.append({"platform": "facebook", "url": self.social_links.facebook})
            
        # Projects
        for p in self.projects:
            if p.links.github:
                targets.append({"platform": "github", "url": p.links.github})
            if p.links.demo:
                targets.append({"platform": "portfolio", "url": p.links.demo})
                
        # Deduplicate by URL
        seen_urls = set()
        unique_targets = []
        for t in targets:
            if t["url"] not in seen_urls:
                seen_urls.add(t["url"])
                unique_targets.append(t)
                
        return unique_targets