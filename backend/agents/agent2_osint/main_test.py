import json
import os
from mock_generator import generate_batch_cvs
from osint_agent import run_agent_2

if __name__ == "__main__":
    # 1. Đảm bảo đã có file mock data
    if not os.path.exists('mock_50_cvs.json'):
        print("Đang tạo file mock data mới...")
        cv_50_list = generate_batch_cvs(50)
        with open('mock_50_cvs.json', 'w', encoding='utf-8') as f:
            json.dump(cv_50_list, f, ensure_ascii=False, indent=4)

    # 2. Đọc 50 CV từ file
    with open('mock_50_cvs.json', 'r', encoding='utf-8') as f:
        batch_cvs = json.load(f)

    print(f"🚀 Bắt đầu xử lý hàng loạt {len(batch_cvs)} CV...")
    all_results = []

    # 3. Cho Agent 2 xử lý
    for cv in batch_cvs:
        print(f"\n---> Đang cào dữ liệu cho: {cv['candidate_id']}")
        result = run_agent_2(cv)
        all_results.append(result)

    # 4. Xuất kết quả
    with open('agent2_final_database.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

    print("\n🎉 XONG! Đã cào xong 50 CV và lưu vào 'agent2_final_database.json'")