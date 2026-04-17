from pydantic import BaseModel, Field
from typing import List, Literal

class VerificationPoint(BaseModel):
    category: str  # e.g., "Skills", "Experience", "Identity"
    claim: str     # Thông tin trong CV
    evidence: str  # Thông tin tìm thấy trên mạng
    status: Literal["Verified", "Warning", "Inconsistent", "No Evidence"]
    reasoning: str # Giải thích tại sao lại đưa ra kết luận đó

class Agent3Output(BaseModel):
    candidate_id: str
    overall_trust_score: float = Field(..., ge=0, le=100)
    verification_details: List[VerificationPoint]
    red_flags: List[str]
    summary_report: str