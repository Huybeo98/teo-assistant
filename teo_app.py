import os
import asyncio
import edge_tts
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from streamlit_mic_recorder import mic_recorder

load_dotenv()

# === THÔNG TIN CÁ NHÂN HOÁ ===
PROFILE = {
    "tên": "Nông Văn Huy",
    "cách gọi": "Anh Huy",
    "chức vụ": "Chuyên viên, Công an xã Phong Dụ Hạ, tỉnh Lào Cai",
    "sở thích": "Ăn hoa quả, đọc sách, giữ gìn trật tự an ninh xã hội",
    "đặc điểm": "Chân thành, cẩn trọng, có trách nhiệm với công việc",
    "mục tiêu": "Phát triển bản thân, phục vụ nhân dân tốt hơn"
}

ASSISTANT_NAME = "TÈO"
VERSION = "3.0 — Trợ lý cá nhân hoá 🎙️🔊"

# === KẾT NỐI API ===
API_KEY = os.getenv("GEMINI_API_KEY", "")
SEARCH_API_KEY = os.getenv("TAVILY_API_KEY", "")

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-3.8-flash")

# === KHỞI TẠO TRẠNG THÁI ===
if "hoi_thoai" not in st.session_state:
    st.session_state.hoi_thoai = []
if "reminders" not in st.session_state:
    st.session_state.reminders = []

# === CÁ NHÂN HOÁ TÍNH CÁCH ===
def get_system_prompt():
    return f"""
Bạn là TÈO — trợ lý cá nhân thông minh, lịch sự và hóm hỉnh của {PROFILE['tên']}.

🎯 **Cách giao tiếp:**
- Lịch sự, tôn trọng, gọi người dùng là "{PROFILE['cách gọi']}"
- Thân thiện như người bạn tin cậy, không trang trọng quá, không dùng lời hoa mỹ, không sến súa
- Hóm hỉnh một cách tinh tế, hài hước phù hợp hoàn cảnh, không quá đùa điên
- Ngắn gọn khi câu hỏi đơn, chi tiết khi vấn đề cần giải thích
- Khi Anh chia sẻ tâm sự: lắng nghe trước, đồng cảm, sau đó đưa góc nhìn và lời khuyên xây dựng — KHÔNG áp đặt, kết thúc bằng "Đó chỉ là góc nhìn của em thôi, Anh tham khảo nhé"
- Khi không chắc chắn: nói thẳng thay vì đoán
- Giữ bí mật mọi điều Anh chia sẻ

👤 **Thông tin về {PROFILE['cách gọi']} — dùng để hỗ trợ phù hợp:**
- Công việc: {PROFILE['chức vụ']}
- Sở thích: {PROFILE['sở thích']}
- Đặc điểm: {PROFILE['đặc điểm']}
- Mục tiêu: {PROFILE['mục tiêu']}

💡 **Hỗ trợ mọi mặt trong cuộc sống:** công việc, học tập, sức khỏe, tâm sự, kế hoạch, giải đáp thắc mắc, tìm kiếm thông tin. Luôn đưa ra phân tích cân bằng và lời khuyên thực tế.
"""

# === CHUYỂN VĂN BẢN → GIỌNG NÓI ===
async def text_to_speech(text, voice="vi-VN-NamMinh"):
    try:
        communicate = edge_tts.Communicate(text, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except Exception as e:
        print(f"Lỗi TTS: {e}")
        return None

# === TÌM KIẾM THÔNG TIN ===
def tim_thong_tin_web(cau_hoi):
    if not SEARCH_API_KEY:
        return None
    try:
        res = requests.post(
            "https://api.tavily.com/search",
            json={"query": cau_hoi, "api_key": SEARCH_API_KEY, "max_results": 2}
        )
        data = res.json()
        if "results" in data and data["results"]:
            return "\n".join([f"• {r['title']}: {r['content']}" for r in data["results"]])
    except:
        pass
    return None

# === SINH CÂU TRẢ LỜI ===
def tra_loi_teo(noi_dung):
    if not API_KEY:
        return "Em chưa được kết nối với bộ não, nhưng em vẫn nghe Anh nói đây. Khi có khóa API, em sẽ thông minh hơn nhiều đấy 😊"
    
    context_prompt = get_system_prompt()
    messages = [{"role": "user", "parts": [context_prompt]}]
    messages.append({"role": "model", "parts": ["Em đã sẵn sàng. Anh muốn nói gì cũng được, em luôn lắng nghe!"]})
    
    for msg in st.session_state.hoi_thoai[-8:]:
        messages.append({"role": msg["vai_tro"], "parts": [msg["noi_dung"]]})
    
    messages.append({"role": "user", "parts": [noi_dung]})
    
    res = model.generate_content(messages, generation_config={"temperature": 0.7, "max_output_tokens": 1024})
    return res.text

# === GIAO DIỆN ===
st.set_page_config(page_title="TÈO — Trợ lý cá nhân", page_icon="🤖", layout="wide")

with st.sidebar:
    st.title("🤖 TÈO")
    st.caption(f"Phiên bản: {VERSION}")
    st.divider()
    
    st.subheader("👤 Thông tin cá nhân")
    st.info(f"""
    🏢 {PROFILE['chức vụ']}
    🍎 {PROFILE['sở thích']}
    """)
    
    st.subheader("🎙️ Cách dùng giọng nói")
    st.markdown("""
    1. Nhấn nút **🎙️ Ghi âm** bên dưới ô nhập liệu
    2. Nói rõ: **"TÈO"** + câu hỏi
    3. Nhấn **⏹️ Dừng** — em sẽ nghe, hiểu và trả lời bằng giọng nói ✅
    """)
    
    st.subheader("⏰ Nhắc nhở")
    if st.session_state.reminders:
        for r in st.session_state.reminders:
            st.write(f"📌 {r['thoi_gian']} — {r['noi_dung']}")
    else:
        st.write("Chưa có nhắc nhở nào")
    
    tg = st.text_input("Thời gian", placeholder="VD: 25/11 18:00")
    nd = st.text_input("Nội dung nhắc")
    if st.button("✅ Lưu") and tg and nd:
        st.session_state.reminders.append({"thoi_gian": tg, "noi_dung": nd})
        st.success("Đã lưu ✅")
        st.rerun()

st.markdown("""
<style>
    .stAudio { width: 100%; }
    .big-font { font-size:18px !important; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 TÈO — Trợ lý cá nhân của Anh Huy")
st.caption("🎙️ Nhấn nút micro để nói, hoặc gõ chữ trực tiếp. Bắt đầu bằng 'TÈO' để em trả lời nhé!")

# === HIỂN THỊ LỊCH SỬ ===
for msg in st.session_state.hoi_thoai:
    with st.chat_message(msg["vai_tro"], avatar="👤" if msg["vai_tro"] == "user" else "🤖"):
        st.write(msg["noi_dung"])
        if msg["vai_tro"] == "assistant" and "audio_reply" in msg and msg["audio_reply"]:
            st.audio(msg["audio_reply"], format="audio/mp3")

# === KHU VỰC GHI ÂM ===
st.divider()
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**🎙️ Nói với TÈO:**")
    recorded_audio = mic_recorder(
        start_prompt="⏺️ Bắt đầu nói",
        stop_prompt="⏹️ Dừng lại",
        key="recorder",
        format="webm"
    )
with col2:
    st.markdown("**Hoặc gõ chữ:**")

# === Ô NHẬP CHỮ ===
cau_hoi_text = st.chat_input("Gõ 'TÈO' + câu hỏi...")

# === XỬ LÝ GHI ÂM ===
if recorded_audio:
    st.info("🔄 Em đang nghe và chuyển thành chữ...")
    audio_bytes = recorded_audio["bytes"]
    
    # Lưu file tạm
    with open("temp_audio.webm", "wb") as f:
        f.write(audio_bytes)
    
    # Sử dụng Google Speech Recognition qua Gemini
    try:
        prompt = "Viết lại nội dung người dùng nói trong tệp âm thanh này, chỉ ghi nội dung, không thêm lời khác:"
        audio_file = genai.upload_file("temp_audio.webm")
        transcript = model.generate_content([prompt, audio_file]).text.strip()
        os.remove("temp_audio.webm")
        
        st.session_state.hoi_thoai.append({"vai_tro": "user", "noi_dung": transcript})
        with st.chat_message("user", avatar="👤"):
            st.write(transcript)
        
        if "tèo" not in transcript.lower():
            st.caption("🔇 (Chưa gọi tên em — em lắng nghe thôi nhé)")
            st.stop()
        
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤖 Em suy nghĩ..."):
                search_result = tim_thong_tin_web(transcript)
                full_query = transcript + (f"\n[Thông tin tìm được: {search_result}]" if search_result else "")
                cau_tra_loi = tra_loi_teo(full_query)
            
            st.write(cau_tra_loi)
            
            with st.spinner("🔊 Em đang nói..."):
                try:
                    audio_output = asyncio.run(text_to_speech(cau_tra_loi))
                    if audio_output:
                        st.audio(audio_output, format="audio/mp3")
                except Exception as e:
                    st.info("🔊 Không thể phát âm thanh trên trình duyệt web, nhưng em vẫn trả lời bằng chữ ở trên nhé")
            
            st.session_state.hoi_thoai.append({
                "vai_tro": "assistant",
                "noi_dung": cau_tra_loi,
                "audio_reply": audio_output if 'audio_output' in locals() else None
            })
    
    except Exception as e:
        st.error(f"Lỗi xử lý giọng nói: {str(e)}. Anh thử gõ chữ nhé!")

# === XỬ LÝ GÕ CHỮ ===
if cau_hoi_text:
    st.session_state.hoi_thoai.append({"vai_tro": "user", "noi_dung": cau_hoi_text})
    with st.chat_message("user", avatar="👤"):
        st.write(cau_hoi_text)
    
    if "tèo" not in cau_hoi_text.lower():
        st.caption("🔇 (Chưa gọi tên em — em lắng nghe thôi nhé)")
        st.stop()
    
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🤖 Em suy nghĩ..."):
            search_result = tim_thong_tin_web(cau_hoi_text)
            full_query = cau_hoi_text + (f"\n[Thông tin tìm được: {search_result}]" if search_result else "")
            cau_tra_loi = tra_loi_teo(full_query)
        
        st.write(cau_tra_loi)
        
        with st.spinner("🔊 Em đang tạo giọng nói..."):
            try:
                audio_output = asyncio.run(text_to_speech(cau_tra_loi))
                if audio_output:
                    st.audio(audio_output, format="audio/mp3")
            except Exception as e:
                st.info("🔊 Trên web không phát được âm thanh, Anh thử trên máy tính cục bộ nhé!")
        
        st.session_state.hoi_thoai.append({
            "vai_tro": "assistant",
            "noi_dung": cau_tra_loi,
            "audio_reply": audio_output if 'audio_output' in locals() else None
        })
