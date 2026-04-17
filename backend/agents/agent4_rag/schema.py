"""
schema.py — Qdrant payload schema for Agent 4 (Competitive Profiler).

Defines CandidatePayload: the structured data stored alongside each CV's
embedding vector in the Qdrant `resumes` collection.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CandidatePayload:
    """
    Structured payload stored in Qdrant for each candidate CV.

    Matches the schema defined in plans/plan_agent4.md:

        {
            "candidate_id": "uuid-string",
            "job_title": "Data Scientist",
            "batch_id": "GDGOC_Hackathon_2026",
            "years_of_experience": 1.5,
            "skills": {
                "core": ["Python", "Machine Learning", "SQL"],
                "tools": ["Git", "Docker"]
            },
            "education": {
                "level": "Undergraduate",
                "major": "Data Science"
            }
        }
    """

    candidate_id: str
    job_title: str
    batch_id: str
    years_of_experience: float
    skills: dict  # {"core": list[str], "tools": list[str]}
    education: dict  # {"level": str, "major": str}

    # ── Post-init validation ──────────────────────────────────────────────────

    def __post_init__(self) -> None:
        # Coerce numeric type — Gemini sometimes returns int or str
        self.years_of_experience = float(self.years_of_experience)

        # Normalise skills dict
        if not isinstance(self.skills, dict):
            self.skills = {"core": [], "tools": []}
        self.skills.setdefault("core", [])
        self.skills.setdefault("tools", [])

        # Normalise education dict
        if not isinstance(self.education, dict):
            self.education = {"level": "Unknown", "major": "Unknown"}
        self.education.setdefault("level", "Unknown")
        self.education.setdefault("major", "Unknown")

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for Qdrant point payload."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CandidatePayload":
        """
        Construct from a plain dict (e.g. a Qdrant scroll result payload).
        Unknown extra keys are silently ignored.
        """
        return cls(
            candidate_id=data["candidate_id"],
            job_title=data["job_title"],
            batch_id=data["batch_id"],
            years_of_experience=data.get("years_of_experience", 0.0),
            skills=data.get("skills", {"core": [], "tools": []}),
            education=data.get("education", {"level": "Unknown", "major": "Unknown"}),
        )