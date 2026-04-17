"""
schema.py — Structured data schema for Agent 3 (Verifier Agent).

Defines the Agent3Output and VerificationPoint dataclasses to format
the cross-verification report and trust score.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class VerificationPoint:
    category: str       # e.g., "Skills", "Experience", "Identity"
    claim: str          # Thông tin trong CV
    evidence: str       # Thông tin tìm thấy trên mạng
    status: str         # "VERIFIED" | "WARNING" | "INCONSISTENT" | "NO_EVIDENCE"
    reasoning: str      # Giải thích tại sao lại đưa ra kết luận đó

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerificationPoint":
        return cls(
            category=data.get("category", "Unknown"),
            claim=data.get("claim", ""),
            evidence=data.get("evidence", ""),
            status=data.get("status", "NO_EVIDENCE"),
            reasoning=data.get("reasoning", ""),
        )


@dataclass
class Agent3Output:
    candidate_id: str
    overall_trust_score: float  # 0-100
    verification_details: list[VerificationPoint]
    red_flags: list[str]
    summary_report: str

    # ── Post-init validation ──────────────────────────────────────────────────

    def __post_init__(self) -> None:
        self.overall_trust_score = float(self.overall_trust_score)
        
        # Đảm bảo list chứa các object VerificationPoint hợp lệ
        if not isinstance(self.verification_details, list):
            self.verification_details = []
        else:
            parsed_details = []
            for item in self.verification_details:
                if isinstance(item, dict):
                    parsed_details.append(VerificationPoint.from_dict(item))
                elif isinstance(item, VerificationPoint):
                    parsed_details.append(item)
            self.verification_details = parsed_details

        if not isinstance(self.red_flags, list):
            self.red_flags = []

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for saving to DB or pipeline state."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Agent3Output":
        """Construct from a plain dict (e.g. parsed JSON from Gemini)."""
        return cls(
            candidate_id=data.get("candidate_id", "unknown_id"),
            overall_trust_score=data.get("overall_trust_score", 0.0),
            verification_details=data.get("verification_details", []),
            red_flags=data.get("red_flags", []),
            summary_report=data.get("summary_report", ""),
        )