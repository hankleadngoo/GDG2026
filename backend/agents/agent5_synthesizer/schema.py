from typing import List, Literal
from pydantic import BaseModel, Field

class EvaluationMetric(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Điểm đánh giá năng lực tổng quan (0-100)")
    reasoning: str = Field(..., description="Lý do cho điểm số này")

class Agent5Output(BaseModel):
    candidate_id: str = Field(..., description="ID của ứng viên")
    overall_evaluation: EvaluationMetric = Field(..., description="Đánh giá tổng quan")
    
    # Suy luận tự động của AI
    inferred_strengths: List[str] = Field(..., description="3-5 điểm mạnh cốt lõi được suy luận từ toàn bộ dữ liệu")
    inferred_weaknesses: List[str] = Field(..., description="Những rủi ro, điểm yếu hoặc lỗ hổng trong hồ sơ")
    
    # Đối chiếu mặt bằng chung
    market_comparison_notes: str = Field(..., description="Nhận xét sự phù hợp của ứng viên so với mặt bằng chung (từ Agent 4)")
    
    # Quyết định
    final_decision: Literal["HIRE", "INTERVIEW_HIGH_PRIORITY", "INTERVIEW_STANDARD", "REJECT", "NEED_MORE_INFO"] = Field(...)
    
    # Báo cáo
    hr_internal_notes: str = Field(..., description="Lưu ý bí mật dành riêng cho nhà tuyển dụng (cảnh báo gian lận, kỹ năng cần xoáy sâu khi phỏng vấn...)")
    candidate_feedback_email: str = Field(..., description="Bản nháp email phản hồi lịch sự, mang tính xây dựng gửi cho ứng viên")