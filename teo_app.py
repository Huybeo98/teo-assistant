import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import requests

load_dotenv()

ASSISTANT_NAME = "TÈO"
VERSION = "2.4 — Nói chuyện tự do 😄"

USER_INFO = {
    "ho_ten": "Nông Văn Huy",
    "ten_gọi": "Anh Huy",
    "don_vi": "Công an xã Phong Dụ Hạ, Công an tỉnh Lào Cai",
    "chuc_vu": "Chuyên viên",
    "cap_bac": "Thượng úy",
    "so_thuong_hieu": "Thích ăn hoa quả 🍎🍊",
    "so_dien_thoai": "0356191555"
}

API_KEY = os.getenv("GEMINI_API_KEY", "")
SEARCH_API_KEY = os.getenv("TAVILY_API_KEY", "")

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-3.8-flash")

if "hoi_thoai" not in st.session_state:
    st.session_state.hoi_thoai = []
if "reminders" not in st.session_state:
    st.session_state.reminders = []

def get_persona_prompt():
    return """
Em là TÈO, trợ lý cá nhân của Anh Huy. Gọi Anh là "Anh Huy".
Phong cách: Hóm hỉnh, hài hước, trang nhã — không sến súa. Nói ngắn gọn, tự nhiên như bạn bè.
Có thể trò chuyện về mọi chủ đề: đời sống, công việc, chia sẻ tâm sự, giải đáp thắc mắc — đều được.
Khi đưa ra lời khuyên: Phân tích rõ, kết thúc bằng "Đó chỉ là góc nhìn của em thôi, Anh tham khảo nhé 😊"
Giữ bí mật mọi thông tin Anh chia sẻ. Không dùng quá nhiều biểu tượng cảm xúc.
"""

def co_goi_ten_teo(noi_dung):
    return "tèo" in noi_dung.lower()

def tim_thong_tin_web(cau_hoi):
    if not SEARCH_API_KEY:
        return "🔎 Chưa cấu hình API tìm kiếm, nhưng em vẫn trò chuyện với Anh được bình thường nhé!"
    try:
        res = requests.post(
            "https://api.tavily.com/search",
            json={"query": cau_hoi, "api_key": SEARCH_API_KEY, "max_results": 3}
        )
        data = res.json()
        if "results" in data and data["results"]:
            return "📋 Thông tin em tìm được:\n" + "\n".join([f"- {r['title']}: {r['content']}" for r in data["results"]])
        return "Không tìm thấy thông tin phù hợp lắm, nhưng em vẫn trò chuyện với Anh được mà 😊"
    except Exception as e:
        return f"Lỗi tìm kiếm, nhưng em vẫn nghe Anh nói đây 😄"

def tra_loi_teo(noi_dung):
    if not API_KEY:
        return "⚠️ Chưa cấu hình API Anh nhé. Khi có khóa, em sẽ thông minh và nói chuyện hay hơn nhiều đấy! 😊"
    
    cau_truc = [{"role": "user", "parts": [get_persona_prompt()]}]
    cau_truc.append({"role": "model", "parts": ["Em là TÈO. Hóm hỉnh, lịch sự, không sến súa. Anh muốn nói gì cũng được, em luôn lắng nghe! 😊"]})
    
    for msg in st.session_state.hoi_thoai[-10:]:
        cau_truc.append({"role": msg["vai_tro"], "parts": [msg["noi_dung"]]})
    
    cau_truc.append({"role": "user", "parts": [noi_dung]})
    
    res = model.generate_content(cau_truc, generation_config={"temperature": 0.8})
    return res.text

st.set_page_config(page_title="TÈO — Trợ lý cá nhân", page_icon="🤖", layout="wide")

with st.sidebar:
    st.title("🤖 TÈO")
    st.caption(f"Phiên bản: {VERSION}")
    st.info("💡 Bắt đầu tin nhắn bằng **'TÈO'** rồi hỏi bất kỳ điều gì nhé!")
    st.divider()
    st.subheader("👤 Thông tin")
    st.info(f"""
    🏢 {USER_INFO['don_vi']}
    📞 {USER_INFO['so_dien_thoai']}
    🍎 {USER_INFO['so_thuong_hieu']}
    """)
    st.subheader("🔗 Truy cập nhanh")
    st.markdown("[📋 Quản lý Văn bản & Công việc](https://quanlyvanbancongviec-3.onrender.com)")
    st.subheader("⏰ Nhắc nhở")
    if st.session_state.reminders:
        for r in st.session_state.reminders:
            st.write(f"📌 {r['thoi_gian']} — {r['noi_dung']}")
    else:
        st.write("Chưa có nhắc nhở nào")
    st.divider()
    tg = st.text_input("Thời gian", placeholder="VD: 25/11 15:30")
    nd = st.text_input("Nội dung nhắc")
    if st.button("✅ Lưu") and tg and nd:
        st.session_state.reminders.append({"thoi_gian": tg, "noi_dung": nd})
        st.success("Đã lưu ✅")
        st.rerun()

st.title("💬 TÈO — Nói chuyện cùng Anh Huy")
st.caption("💡 Gõ **'TÈO'** + câu hỏi → em trả lời mọi điều Anh muốn biết. Cứ nói tự nhiên nhé! 😊")

for msg in st.session_state.hoi_thoai:
    with st.chat_message(msg["vai_tro"]):
        st.write(msg["noi_dung"])

cau_hoi = st.chat_input("Nhập 'TÈO' rồi nói gì đó...")

if cau_hoi:
    st.session_state.hoi_thoai.append({"vai_tro": "user", "noi_dung": cau_hoi})
    with st.chat_message("user"):
        st.write(cau_hoi)
    
    if not co_goi_ten_teo(cau_hoi):
        st.caption("🔇 (Chưa gọi tên em, em lắng nghe thôi nhé)")
        st.stop()
    
    if any(tu in cau_hoi.lower() for tu in ["tìm", "kiếm", "thông tin", "tin tức", "thế nào", "mấy giờ", "thời tiết"]):
        with st.chat_message("assistant"):
            with st.spinner("🔎 Để em xem..."):
                ket_qua = tim_thong_tin_web(cau_hoi)
                st.write(ket_qua)
                st.session_state.hoi_thoai.append({"vai_tro": "model", "noi_dung": ket_qua})
    else:
        with st.chat_message("assistant"):
            with st.spinner("🤖 Em đang lắng nghe..."):
                tra_loi = tra_loi_teo(cau_hoi)
                st.write(tra_loi)
                st.session_state.hoi_thoai.append({"vai_tro": "model", "noi_dung": tra_loi})
