"""
Pydantic v2 schema for Agent 1 output.

This is the canonical data contract between Agent 1 (Extractor) and the
downstream agents:
  - Agent 2 (OSINT): consumes `candidate`, `social_links`, `projects[].links`,
    `work_experience[].company_url`
  - Agent 3 (Verifier): consumes the full object to cross-check OSINT results
    against CV claims
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


# ---------------------------------------------------------------------------
# Leaf models
# ---------------------------------------------------------------------------


class CandidateInfo(BaseModel):
    full_name: str = Field(..., description="Candidate's full name as written in the CV")
    email: Optional[str] = Field(None, description="Primary email address")
    phone: Optional[str] = Field(None, description="Primary phone number, including country code if present")
    location: Optional[str] = Field(None, description="City, country, or full address as stated")
    summary: Optional[str] = Field(None, description="Professional summary or objective, verbatim or lightly cleaned")


class SocialLinks(BaseModel):
    linkedin: Optional[str] = Field(None, description="Full LinkedIn profile URL")
    github: Optional[str] = Field(None, description="Full GitHub profile URL")
    facebook: Optional[str] = Field(None, description="Full Facebook profile URL")
    portfolio: Optional[str] = Field(None, description="Personal website or portfolio URL")
    other: List[str] = Field(default_factory=list, description="Any other URLs found in the CV")


class Education(BaseModel):
    institution: str = Field(..., description="Name of university, college, or school")
    degree: Optional[str] = Field(None, description="e.g. Bachelor of Science, High School Diploma")
    major: Optional[str] = Field(None, description="Field of study or major")
    gpa: Optional[str] = Field(None, description="GPA or grade as written, e.g. '3.8/4.0' or '8.5/10'")
    start_year: Optional[int] = Field(None, ge=1950, le=2100)
    end_year: Optional[int] = Field(None, ge=1950, le=2100, description="Use null if still enrolled")


class ProjectLinks(BaseModel):
    github: Optional[str] = Field(None, description="GitHub repo URL for this project")
    demo: Optional[str] = Field(None, description="Live demo or deployed URL")
    other: List[str] = Field(default_factory=list, description="Any other project-related URLs")


class Project(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Short description of the project and its purpose")
    tech_stack: List[str] = Field(default_factory=list, description="Languages, frameworks, tools used")
    links: ProjectLinks = Field(default_factory=ProjectLinks)
    role: Optional[str] = Field(None, description="Candidate's role if a team project, e.g. 'Backend developer'")


class WorkExperience(BaseModel):
    company: str = Field(..., description="Employer name")
    role: str = Field(..., description="Job title or position")
    start_date: Optional[str] = Field(None, description="Start date as written, e.g. 'Jan 2022' or '2022-01'")
    end_date: Optional[str] = Field(None, description="End date as written; null or 'Present' if current")
    is_current: bool = Field(False, description="True if this is the candidate's current job")
    responsibilities: List[str] = Field(default_factory=list, description="Key bullet points or responsibilities")
    company_url: Optional[str] = Field(None, description="Company website URL if mentioned in CV")


class Skills(BaseModel):
    languages: List[str] = Field(default_factory=list, description="Programming languages, e.g. Python, TypeScript")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks & libraries, e.g. React, FastAPI")
    tools: List[str] = Field(default_factory=list, description="Tools & platforms, e.g. Docker, Git, AWS")
    other: List[str] = Field(default_factory=list, description="Anything that doesn't fit above, e.g. Agile, JIRA")


class Certification(BaseModel):
    name: str = Field(..., description="Certificate or course name")
    issuer: Optional[str] = Field(None, description="Issuing organization, e.g. Google, Coursera, AWS")
    year: Optional[int] = Field(None, ge=1990, le=2100)
    url: Optional[str] = Field(None, description="Verification or credential URL if provided")


class LanguageSpoken(BaseModel):
    language: str = Field(..., description="e.g. English, Vietnamese, Japanese")
    proficiency: Optional[str] = Field(
        None,
        description="Level as stated, e.g. Native, Fluent, B2, IELTS 7.0",
    )


class ExtractionMetadata(BaseModel):
    source_file: str = Field(..., description="Original file name or 'plaintext' for raw string input")
    parse_method: Literal["llamaparse", "docx", "plaintext", "pymupdf_fallback"] = Field(
        ..., description="Which parser produced the raw text"
    )
    extraction_model: str = Field("gemini-1.5-pro", description="LLM used for structured extraction")
    extracted_at: str = Field(..., description="ISO-8601 UTC datetime when extraction ran")
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal issues: fallback used, fields that could not be parsed, etc.",
    )


# ---------------------------------------------------------------------------
# Root model
# ---------------------------------------------------------------------------


class CVExtraction(BaseModel):
    """
    Top-level output of Agent 1. Passed verbatim to Agent 2 and Agent 3.

    Design rules:
    - Every field that isn't found in the CV must be null / empty list — never fabricated.
    - URLs are stored as plain strings so they can be serialised to JSON easily.
    - Consumers should treat all Optional fields as potentially null.
    """

    candidate: CandidateInfo
    social_links: SocialLinks = Field(default_factory=SocialLinks)
    education: List[Education] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    certifications: List[Certification] = Field(default_factory=list)
    languages_spoken: List[LanguageSpoken] = Field(default_factory=list)
    metadata: ExtractionMetadata

    # ------------------------------------------------------------------
    # Helpers consumed by downstream agents
    # ------------------------------------------------------------------

    def all_urls(self) -> List[str]:
        """Return every URL found anywhere in the extraction (for Agent 2)."""
        urls: List[str] = []

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

        return list(dict.fromkeys(urls))  # deduplicate, preserve order
    
    def all_urls(self) -> list[str]:
        urls = []
        if self.social_links.linkedin: urls.append(self.social_links.linkedin)
        if self.social_links.github: urls.append(self.social_links.github)
        if self.social_links.portfolio: urls.append(self.social_links.portfolio)
        return [u for u in urls if u]

    def osint_targets(self) -> dict:
        """
        Compact dict of targets for Agent 2 to investigate.
        Keeps the OSINT agent focused without it needing to parse the full schema.
        """
        return {
            "candidate_name": self.candidate.full_name,
            "social_links": {
                "linkedin": self.social_links.linkedin,
                "github": self.social_links.github,
                "facebook": self.social_links.facebook,
                "portfolio": self.social_links.portfolio,
                "other": self.social_links.other,
            },
            "project_links": [
                {
                    "project_name": p.name,
                    "github": p.links.github,
                    "demo": p.links.demo,
                    "other": p.links.other,
                }
                for p in self.projects
                if p.links.github or p.links.demo or p.links.other
            ],
            "employers": [
                {"company": e.company, "url": e.company_url}
                for e in self.work_experience
                if e.company_url
            ],
        }
