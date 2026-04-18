import streamlit as st
import time
from main import agent_1_2_logic, agent_3_logic, agent_4_5_logic

st.set_page_config(page_title="Resume Protector Demo", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! Tôi là **Resume Protector**, hệ thống trợ lý AI chuyên biệt giúp thẩm định và đánh giá hồ sơ ứng viên đa chiều. Bạn cần tôi giúp gì hôm nay?"}
    ]
if "step" not in st.session_state:
    st.session_state.step = "idle"
if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
    
with st.sidebar:
    st.title("Team AE107")
    
    st.markdown("### 1. Tiêu chí tuyển dụng (JD)")
    jd_file = st.file_uploader("Tải lên file JD (PDF, DOCX, TXT)", type=["pdf", "doc", "docx", "txt"], key=f"jd_uploader_{st.session_state.uploader_key}")
    
    if jd_file:
        st.success(f"✅ Đã nhận cấu hình JD: {jd_file.name}")
    st.markdown("---")
    
    st.markdown("### 2. Hồ sơ ứng viên (CV)")
    uploaded_file = st.file_uploader("Tải lên CV (PDF)", type=["pdf"], key=f"uploader_{st.session_state.uploader_key}")
    
    if uploaded_file and st.session_state.step == "idle":
        if not jd_file:
            st.warning("💡 Khuyến nghị: Bạn nên tải lên file JD ở trên để AI có cơ sở đối chiếu chính xác nhất.")
            
        spinner_ph = st.empty()
        
        with spinner_ph:
            with st.spinner("Đọc file pdf..."): 
                time.sleep(2)
        with spinner_ph:
            with st.spinner("Trích đường dẫn..."): 
                time.sleep(2)
        with spinner_ph:
            with st.spinner("Tổng hợp dữ liệu..."):
                time.sleep(2)
                result = agent_1_2_logic(uploaded_file.name)
        
        spinner_ph.empty()
        
        st.session_state.candidate_data = result
        st.session_state.step = "uploaded"
        
        s = result["agent1_summary"]
        c = s["candidate"]
        
        edu = ", ".join([f"{e['major']} @ {e['institution']}" for e in s["education"]])
        exp = ", ".join([f"{e['role']} ({e['company']})" for e in s["work_experience"]])
        sk = ", ".join(s["skills"]["languages"] + s["skills"]["frameworks"])
        pjs = ", ".join([p["name"] for p in s["projects"]])
        aws = ", ".join([a["title"] for a in s["honors_awards"]])
        certs = ", ".join(s["certifications"])
        langs = ", ".join([f"{l['language']} ({l['proficiency']})" for l in s["languages_spoken"]])

        msg = f"""
Tôi đã trích xuất xong hồ sơ của ứng viên **{c['full_name']}**. Dưới đây là thông tin chi tiết:

**🎯 Vị trí:** {c['summary']}

**🎓 Học vấn:** {edu}

**💻 Kỹ năng chuyên môn:** {sk}

**💼 Kinh nghiệm:** {exp}

**🚀 Dự án nổi bật:** {pjs}

**🏆 Giải thưởng:** {aws}

**📜 Chứng chỉ:** {certs}

**🌐 Ngoại ngữ:** {langs}

---
Bạn có muốn tôi tiến hành **đối chiếu và thẩm định chuyên sâu** không?
        """
        st.session_state.messages.append({"role": "assistant", "content": msg})

    if st.session_state.candidate_data:
        st.subheader("🔗 Các đường link liên quan")
        for link in st.session_state.candidate_data["osint_links"]:
            platform = link['platform'].capitalize()
            url = link['url']
            st.markdown(f"""<a href="{url}" target="_blank" style="color: #1E90FF; text-decoration: underline; font-weight: bold;">{platform} Profile</a>""", unsafe_allow_html=True)
        st.markdown("---")

st.header("🤖 Resume Protector")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Nhập tin nhắn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Suy nghĩ câu trả lời..."): 
        time.sleep(2)
    if st.session_state.step == "idle":
        with st.chat_message("assistant"):
            reply = """Hệ thống Resume Protector hoạt động dựa trên luồng 5 Agent chuyên biệt:
1. **Extractor:** Trích xuất dữ liệu có cấu trúc từ CV.
2. **OSINT:** Cào dữ liệu từ Github, LinkedIn...
3. **Verifier:** Đối soát sự thật và tìm mâu thuẫn.
4. **Profiler:** Tham chiếu năng lực với mặt bằng chung.
5. **Evaluator:** Tổng hợp và đưa ra quyết định tuyển dụng.

*Hãy tải lên một CV ở cột bên trái để thử nghiệm nhé!*"""
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

    elif st.session_state.step == "uploaded" and any(w in prompt.lower() for w in ["ok", "có", "tiến hành", "đồng ý", "bắt đầu"]):
        with st.chat_message("assistant"):
            
            spinner_ph = st.empty()
            with spinner_ph:
                with st.spinner("Thu thập dữ liệu từ LinkedIn..."): 
                    time.sleep(2)
            with spinner_ph:
                with st.spinner("Thu thập dữ liệu từ Github..."): 
                    time.sleep(2)
            with spinner_ph:
                with st.spinner("Đối chiếu xác nhận kỹ năng..."): 
                    time.sleep(2)
            with spinner_ph:
                with st.spinner("Đối chiếu xác nhận giải thưởng..."): 
                    time.sleep(2)
            with spinner_ph:
                with st.spinner("Phân tích điểm mâu thuẫn..."):
                    time.sleep(2)
                    a3 = agent_3_logic()
            spinner_ph.empty()
            
            res = "Kết quả đối chiếu so với dữ liệu thu thập\n\n"
            
            for d in a3["verification_details"]:
                status = d['status']
                if status == 'VERIFIED':
                    status_display = f":green[{status}]"
                elif status == 'WARNING':
                    status_display = f":red[{status}]"
                elif status == 'BONUS':
                    status_display = f":orange[{status}]"
                else:
                    status_display = f"**{status}**"
                    
                res += f"**{d['category']}**: {status_display}\n"
                res += f"- *Khai báo:* {d['claim']}\n"
                res += f"- *Bằng chứng:* {d['evidence']}\n\n"
            
            if a3.get("red_flags"):
                res += "---\n🚨 **CẢNH BÁO:**\n"
                for flag in a3["red_flags"]:
                    res += f"- {flag}\n"
            
            st.markdown(res)
            st.session_state.messages.append({"role": "assistant", "content": res})
            st.session_state.step = "verified"
            
    elif st.session_state.step == "verified" and any(w in prompt.lower() for w in ["tuyển", "tuyển dụng", "vào vòng trong", "quyết định"]):
        with st.chat_message("assistant"):
            
            spinner_ph = st.empty()
            with spinner_ph:
                with st.spinner("Thu thập dữ liệu từ cơ sở dữ liệu..."): 
                    time.sleep(2)
            with spinner_ph:
                with st.spinner("So sánh đối chiếu ứng viên..."): 
                    time.sleep(2)
            with spinner_ph:
                with st.spinner("Chuẩn bị quyết định..."):
                    time.sleep(2)
                    eval_data = agent_4_5_logic()
            spinner_ph.empty()
            
            res_eval = f"Đánh giá tổng thể và quyết định\n\n"
            res_eval += f"**💡 Tham chiếu thị trường:** {eval_data['market_comparison']}\n\n"
            res_eval += "---\n**📝 Phân tích Năng lực cốt lõi:**\n\n"
            res_eval += f"- **Kỹ năng:** {eval_data['evaluation']['skills']}\n\n"
            res_eval += f"- **Kinh nghiệm:** {eval_data['evaluation']['experience']}\n\n"
            res_eval += f"- **Dự án:** {eval_data['evaluation']['projects']}\n\n"
            res_eval += "---\n"
            
            decision_raw = eval_data['final_decision']
            if "ACCEPT" in decision_raw:
                decision_colored = f":green[{decision_raw}]"
            else:
                decision_colored = f":red[{decision_raw}]"
                
            res_eval += f"**🎯 ĐỀ XUẤT TỪ HỆ THỐNG:** {decision_colored}\n\n"
            res_eval += f"*{eval_data['recommendation']}*\n\n"

            if "suggested_questions" in eval_data:
                res_eval += "---\n**🗣️ GỢI Ý CÂU HỎI PHỎNG VẤN TỪ AI:**\n"
                for q in eval_data["suggested_questions"]:
                    res_eval += f"- {q}\n"

            st.markdown(res_eval)
            st.session_state.messages.append({"role": "assistant", "content": res_eval})
            st.session_state.step = "evaluated"

if st.session_state.step == "evaluated":
    st.markdown("---")
    
    col_empty, col_accept, col_reject = st.columns([6, 1, 1])
    
    with col_accept:
        if st.button("ACCEPT", use_container_width=True, type="primary"):
            st.toast("Đã lưu ứng viên vào danh sách phỏng vấn!")
            time.sleep(1)
            
            st.session_state.messages.append({"role": "assistant", "content": "✅ **Đã phê duyệt ứng viên.** Bạn có thể tiếp tục tải lên CV tiếp theo ở cột bên trái."})
            
            st.session_state.step = "idle"
            st.session_state.candidate_data = None
            st.session_state.uploader_key += 1
            st.rerun() 
            
    with col_reject:
        if st.button("REJECT", use_container_width=True):
            st.toast("Đã loại ứng viên này.")
            time.sleep(1)
            
            st.session_state.messages.append({"role": "assistant", "content": "❌ **Đã loại ứng viên.** Bạn có thể tiếp tục tải lên CV tiếp theo ở cột bên trái."})
            
            st.session_state.step = "idle"
            st.session_state.candidate_data = None
            st.session_state.uploader_key += 1
            st.rerun() 