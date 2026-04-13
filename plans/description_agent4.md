1. Chiến lược mới cho Agent 4: The Competitive Profiler (Hồ sơ Cạnh tranh)
Trích xuất thông tin từ những CV của những ứng viên khác ở hiện tại và trong quá khứ đã có trong database có liên quan đến công việc đang ứng tuyển của ứng viên. Để làm cơ sở, trung bình chung của toàn bộ ngành, tạo tiêu chuẩn khách quan đánh giá năng lực của ứng viên.

Agent 4 sẽ đóng vai trò đo lường mức độ cạnh tranh của một ứng viên so với toàn bộ Talent Pool (Tập hồ sơ hiện tại). Nó sẽ trả lời câu hỏi: "Trong 100 CV nộp vào vị trí này, ứng viên này đang đứng ở đâu (top 10%, top 50%, hay nhóm yếu nhất)?"

2. Thiết kế Payload Qdrant
Ví dụ:
{
  "candidate_id": "string",
  "job_title": "string (VD: Data Scientist)", // Quan trọng nhất để phân cụm
  "batch_id": "string (VD: GDGOC_Hackathon_2026)", // Dùng để lọc theo đợt tuyển
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

3. Dataflow của Agent 4 (The Competitive Profiler)
Cách Agent 4 hoạt động khi nhận được một CV mới:

Ingestion & Indexing (Nạp & Lập chỉ mục): Mỗi khi Agent 1 trích xuất xong một CV mới, dữ liệu (Vector + Payload) lập tức được đẩy thẳng vào Qdrant.

Aggregation Query (Truy vấn Tổng hợp): Thay vì tìm K-Nearest Neighbors, Agent 4 sẽ yêu cầu Qdrant thực hiện phép toán tổng hợp (Aggregation) trên tất cả các CV có cùng job_title và batch_id.

Ví dụ: Qdrant sẽ tính toán và trả về: Kinh nghiệm trung bình là bao nhiêu năm? Tỷ lệ người biết Python là bao nhiêu %?

LLM Generation (Sinh báo cáo): LLM nhận CV_JSON của ứng viên hiện tại và dữ liệu tổng hợp từ Qdrant để viết báo cáo.
