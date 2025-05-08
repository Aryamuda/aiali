import streamlit as st
import os
from dotenv import load_dotenv
from dashscope import Generation
import dashscope
from PyPDF2 import PdfReader
import pandas as pd
from PIL import Image
import pytesseract

# === LOAD ENV ===
load_dotenv()
DASHSCOPE_API_KEY = st.secrets.get("DASHSCOPE_API_KEY") or os.getenv("DASHSCOPE_API_KEY")

if not DASHSCOPE_API_KEY:
    st.error("❌ No API key found. Set it in .env or Streamlit Secrets as 'DASHSCOPE_API_KEY'.")
    st.stop()

dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'username' not in st.session_state:
    st.session_state.username = None

st.set_page_config(page_title="Chat App", page_icon="🤖")
st.title("🤖 Chat with Memory")
st.markdown("Ask anything")

if not st.session_state.username:
    with st.form("name_form"):
        name = st.text_input("Enter your name:", placeholder="Contoh: John Doe")
        submitted = st.form_submit_button("Start Chat")
        if submitted and name:
            st.session_state.username = name
            st.rerun()
        else:
            st.stop()

# === FILE UPLOAD ===
uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx", "txt", "pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_type = uploaded_file.type
    extracted_text = ""

    try:
        if file_type == "application/pdf":
            pdf_reader = PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() or ""

        elif file_type == "text/csv":
            df = pd.read_csv(uploaded_file)
            extracted_text = df.to_string()

        elif file_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            df = pd.read_excel(uploaded_file)
            extracted_text = df.to_string()

        elif file_type == "text/plain":
            extracted_text = uploaded_file.read().decode("utf-8")

        elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
            image = Image.open(uploaded_file)
            extracted_text = pytesseract.image_to_string(image)

        if extracted_text.strip():
            st.session_state.chat_history.append({
                "role": "system",
                "content": f"Here's the content from the uploaded file:\n{extracted_text}"
            })

    except Exception as e:
        st.warning(f"⚠️ Error while processing file: {str(e)}")

# === RESET CHAT ===
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

# === SHOW HISTORY ===
for msg in st.session_state.chat_history[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === CHAT INPUT ===
user_input = st.chat_input("What's on your mind?")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Im thinking, be patient..."):
        try:
            response = Generation.call(
                api_key=DASHSCOPE_API_KEY,
                model="qwen-plus",
                messages=st.session_state.chat_history,
                result_format="message"
            )

            if response and response.output and hasattr(response.output, "choices"):
                reply = response.output.choices[0].message.content
            else:
                reply = f"⚠️ Gagal dapet balasan dari Dashscope. Cek response: `{response}`"

        except Exception as e:
            reply = f"⚠️ Error pas call Dashscope: {str(e)}"

        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
