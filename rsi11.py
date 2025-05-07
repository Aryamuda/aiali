import streamlit as st
import os
from dotenv import load_dotenv
from dashscope import Generation
import dashscope

# === LOAD .env ===
load_dotenv()
DASHSCOPE_API_KEY = st.secrets.get("DASHSCOPE_API_KEY") or os.getenv("DASHSCOPE_API_KEY")

# === DASHSCOPE BASE URL ===
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

# === INITIALIZE STATE ===
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'username' not in st.session_state:
    st.session_state.username = None

# === UI SETUP ===
st.set_page_config(page_title="Qwen Chat App", page_icon="🤖")
st.title("🤖 Qwen Chat with Memory")
st.markdown("Ask anything. Powered by **Qwen-Plus** ⚡")

# === GET USERNAME ===
if not st.session_state.username:
    with st.form("name_form"):
        st.session_state.username = st.text_input("Masukin nama lu:", placeholder="Contoh: Bro Quant")
        submitted = st.form_submit_button("Start Chat")
        if not submitted:
            st.stop()
    st.rerun()

# === RESET BUTTON ===
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔁 Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

# === SYSTEM PROMPT ===
if not st.session_state.chat_history:
    st.session_state.chat_history.append({
        "role": "system",
        "content": f"Kamu adalah asisten pribadi buat {st.session_state.username}, bantu dia sebaik mungkin."
    })

# === SHOW CHAT HISTORY ===
for msg in st.session_state.chat_history[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === INPUT HANDLER ===
user_input = st.chat_input("Tulis pertanyaanmu...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Qwen mikir..."):
        try:
            response = Generation.call(
                api_key=DASHSCOPE_API_KEY,
                model="qwen-plus",
                messages=st.session_state.chat_history,
                result_format='message'
            )
            reply = response.output.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ Error: {str(e)}"

        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
