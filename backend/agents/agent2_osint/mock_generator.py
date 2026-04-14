import random
import json

def generate_batch_cvs(num_cvs=50):
    """Sinh ra danh sách JSON chứa nhiều CV với các trạng thái link ngẫu nhiên."""
    mock_url_database = {
        "github": [
            "https://github.com/torvalds",           
            "https://github.com/yyx990803",          
            "https://github.com/karpathy",           
            "https://github.com/invalid_user_99999", 
            "https://github.com"                     
        ],
        "linkedin": [
            "https://linkedin.com/in/nguyenvana123",        
            "https://www.linkedin.com/in/williamhgates",    
            "https://linkedin.com/in/not-exist-404-error"   
        ],
        "portfolio": [
            "https://portfolio-nguyenvana.vercel.app", 
            "https://github.blog",                     
            "https://example-broken-link.com",         
            "https://my-awesome-cv-error.com"          
        ]
    }

    batch_data = []
    for i in range(1, num_cvs + 1):
        candidate_id = f"CV_IT_{str(i).zfill(3)}"
        num_links = random.randint(1, 3)
        chosen_platforms = random.sample(["github", "linkedin", "portfolio"], num_links)

        extracted_links = [{"platform": p, "url": random.choice(mock_url_database[p])} for p in chosen_platforms]

        batch_data.append({
            "candidate_id": candidate_id,
            "extracted_links": extracted_links
        })

    return batch_data

if __name__ == "__main__":
    print("⏳ Đang tiến hành tạo 50 CV giả lập...")
    cv_50_list = generate_batch_cvs(50)
    with open('mock_50_cvs.json', 'w', encoding='utf-8') as f:
        json.dump(cv_50_list, f, ensure_ascii=False, indent=4)
    print("✅ Đã xuất thành công file 'mock_50_cvs.json'.")