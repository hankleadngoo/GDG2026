import json
import os
import sys

# Đảm bảo Python nhận diện được các thư mục con
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------
# QUAN TRỌNG: IMPORT HÀM LÕI CỦA AGENT 1
# Bạn hãy mở file agents/agent1_extractor/extract_data.py ra xem
# đồng đội của bạn đặt tên cái hàm nhận file PDF vào là gì nhé!
# (Ở đây tôi đang giả sử tên hàm là 'process_pdf_to_json')
# ---------------------------------------------------------
from agents.agent1_extractor.parser import parse_cv

# Import Agent 2
from agents.agent2_osint.osint_agent import run_agent_2

def adapter_agent1_to_agent2(cv_result_data, filename):
    """
    Hàm cầu nối: Chuyển đổi Output Agent 1 -> Input Agent 2
    """
    extracted_links = []
    
    # Tùy thuộc vào code của Agent 1 trả về cấu trúc thế nào, 
    # thường nó sẽ bọc trong key "result" hoặc "social_links"
    socials = cv_result_data.get("social_links", {}) 
    if not socials and "result" in cv_result_data:
        socials = cv_result_data["result"].get("social_links", {})
        
    for platform in ["github", "linkedin", "facebook", "portfolio"]:
        url = socials.get(platform)
        if url: 
            extracted_links.append({"platform": platform, "url": url})

    return {
        "candidate_id": filename,
        "extracted_links": extracted_links
    }

def run_real_cv(pdf_path):
    print("="*70)
    print(f"🚀 BẮT ĐẦU PHÂN TÍCH CV: {os.path.basename(pdf_path)}")
    print("="*70)

    # ==========================================
    # GIAI ĐOẠN 1: AGENT 1 ĐỌC PDF
    # ==========================================
    print("\n🤖 [AGENT 1] Đang đọc file PDF và dùng AI để bóc tách dữ liệu...")
    try:
        # Gọi hàm của Agent 1 (Truyền đường dẫn file PDF vào)
        agent1_output = parse_cv(pdf_path)
        print("   ✅ [AGENT 1] Bóc tách thành công!")
    except Exception as e:
        print(f"   ❌ [AGENT 1] Lỗi khi đọc PDF: {e}")
        return

    # ==========================================
    # GIAI ĐOẠN 2: CHUYỂN ĐỔI DỮ LIỆU
    # ==========================================
    filename = os.path.basename(pdf_path)
    agent2_input = adapter_agent1_to_agent2(agent1_output, filename)
    
    if len(agent2_input['extracted_links']) == 0:
        print("\n⚠️ [HỆ THỐNG] Không tìm thấy link mạng xã hội nào trong CV. Kết thúc quy trình.")
        return
        
    print(f"\n🔗 Đã tìm thấy {len(agent2_input['extracted_links'])} link để cào: {agent2_input['extracted_links']}")

    # ==========================================
    # GIAI ĐOẠN 3: AGENT 2 CÀO DỮ LIỆU
    # ==========================================
    print("\n🤖 [AGENT 2] Bắt đầu kích hoạt hệ thống Crawler...")
    try:
        osint_result = run_agent_2(agent2_input)
        print("   ✅ [AGENT 2] Cào dữ liệu chuyên sâu hoàn tất!")
    except Exception as e:
        print(f"   ❌ [AGENT 2] Lỗi cào dữ liệu: {e}")
        return

    # ==========================================
    # XUẤT KẾT QUẢ CUỐI CÙNG
    # ==========================================
    output_filename = f"FINAL_REPORT_{filename}.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(osint_result, f, ensure_ascii=False, indent=4)
        
    print("\n" + "="*70)
    print(f"🎉 HOÀN TẤT PIPELINE THỰC TẾ! Toàn bộ dữ liệu đã lưu vào: {output_filename}")
    print("="*70)

if __name__ == "__main__":
    # Thay tên file này bằng đúng tên file CV của bạn
    my_cv_path = "data/CV_Pham_Tien_Dung_DSAI.pdf" 
    
    if os.path.exists(my_cv_path):
        run_real_cv(my_cv_path)
    else:
        print(f"❌ Không tìm thấy file CV tại đường dẫn: {my_cv_path}")