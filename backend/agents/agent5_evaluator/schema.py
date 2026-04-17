"""
schema.py — Structured data schema for Agent 5 (Final Evaluator).

Defines the Agent5Output and EvaluationMetric dataclasses to strictly format
the LLM's final decision before passing it back to the pipeline state or UI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class EvaluationMetric:
    score: int
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Agent5Output:
    """
    Structured payload representing the final HR evaluation.
    """
    candidate_id: str
    overall_evaluation: EvaluationMetric
    inferred_strengths: list[str]
    inferred_weaknesses: list[str]
    market_comparison_notes: str
    final_decision: str  # e.g., HIRE, REJECT, INTERVIEW
    hr_internal_notes: str
    candidate_feedback_email: str

    # ── Post-init validation ──────────────────────────────────────────────────

    def __post_init__(self) -> None:
        # Ép kiểu an toàn trong trường hợp LLM trả về sai type cơ bản
        if isinstance(self.overall_evaluation, dict):
            self.overall_evaluation = EvaluationMetric(**self.overall_evaluation)
            
        if not isinstance(self.inferred_strengths, list):
            self.inferred_strengths = []
            
        if not isinstance(self.inferred_weaknesses, list):
            self.inferred_weaknesses = []

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for saving to DB or returning to UI."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Agent5Output":
        """
        Construct from a plain dict (e.g. parsed JSON from Gemini).
        Unknown extra keys are silently ignored.
        """
        eval_data = data.get("overall_evaluation", {"score": 0, "reasoning": "Unknown"})
        
        return cls(
            candidate_id=data.get("candidate_id", "unknown_id"),
            overall_evaluation=EvaluationMetric(**eval_data),
            inferred_strengths=data.get("inferred_strengths", []),
            inferred_weaknesses=data.get("inferred_weaknesses", []),
            market_comparison_notes=data.get("market_comparison_notes", ""),
            final_decision=data.get("final_decision", "NEED_MORE_INFO"),
            hr_internal_notes=data.get("hr_internal_notes", ""),
            candidate_feedback_email=data.get("candidate_feedback_email", ""),
        )