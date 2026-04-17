import json
import os
import sys

# Đảm bảo Python nhận diện được thư mục agents để import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.agent2_osint.osint_agent import run_agent_2

def adapter_agent1_to_agent2(cv_result, filename):
    """
    Hàm cầu nối (Adapter): Chuyển đổi Output Agent 1 -> Input Agent 2
    Chỉ lấy link thật, tuyệt đối không tự bịa dữ liệu.
    """
    extracted_links = []
    socials = cv_result.get("social_links", {})
    
    # Trích xuất link thật từ CV
    for platform in ["github", "linkedin", "facebook", "portfolio"]:
        url = socials.get(platform)
        if url: # Chỉ thêm vào nếu url khác null hoặc rỗng
            extracted_links.append({"platform": platform, "url": url})

    return {
        "candidate_id": filename,
        "extracted_links": extracted_links
    }

def run_pipeline():
    print("="*70)
    print("🚀 KHỞI ĐỘNG PIPELINE: AGENT 1 (Trích xuất) -> AGENT 2 (OSINT)")
    print("="*70)

    agent1_output_path = "agents/agent1_extractor/demo_output.json"
    
    if not os.path.exists(agent1_output_path):
        print(f"❌ LỖI: Không tìm thấy file {agent1_output_path}")
        return
        
    with open(agent1_output_path, "r", encoding="utf-8") as f:
        agent1_data = json.load(f)
        
    samples = agent1_data.get("demo_samples", [])
    print(f"📦 Đã tải {len(samples)} hồ sơ từ Agent 1.\n")

    all_osint_results = []

    # Duyệt qua từng hồ sơ
    for index, sample in enumerate(samples):
        # 1. BỎ QUA CÁC CV BỊ LỖI TRÍCH XUẤT
        if sample.get("status") != "ok":
            print(f"⏭️ Bỏ qua hồ sơ [{index}] do Agent 1 báo lỗi trích xuất.")
            continue
            
        cv_result = sample.get("result", {})
        candidate_name = cv_result.get('candidate', {}).get('full_name', 'Unknown')
        filename = sample.get("file", f"CV_UNKNOWN_{index}")
        
        print(f"\n▶️ ĐANG XỬ LÝ HỒ SƠ: {candidate_name}")
        
        # Gọi Adapter (CHỈ LẤY LINK THẬT)
        agent2_input = adapter_agent1_to_agent2(cv_result, filename)
        
        # 2. LOGIC MỚI: NẾU KHÔNG CÓ LINK NÀO -> BỎ QUA CV NÀY LUÔN
        if len(agent2_input['extracted_links']) == 0:
            print("   ⚠️ Không tìm thấy link mạng xã hội nào trong CV. Bỏ qua và sang người tiếp theo!")
            continue
            
        print(f"   🔗 Đã tìm thấy {len(agent2_input['extracted_links'])} link thật để cào.")

        # 3. KÍCH HOẠT AGENT 2 (Chỉ chạy khi có link)
        print("   ⏳ Đang kích hoạt Crawler...")
        osint_result = run_agent_2(agent2_input)
        all_osint_results.append(osint_result)
        print("   ✅ Cào dữ liệu thành công!")

    # ==========================================
    # KẾT THÚC PIPELINE & LƯU KẾT QUẢ
    # ==========================================
    print("\n" + "="*70)
    if all_osint_results:
        output_file = "pipeline_final_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_osint_results, f, ensure_ascii=False, indent=4)
        print(f"🎉 PIPELINE HOÀN TẤT! Đã cào thành công {len(all_osint_results)} ứng viên có link và lưu vào: {output_file}")
    else:
        print("⚠️ PIPELINE HOÀN TẤT! Đã quét qua toàn bộ CV nhưng không có ứng viên nào để lại link hợp lệ.")
    print("="*70)

if __name__ == "__main__":
    run_pipeline()