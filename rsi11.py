import streamlit as st
import os
from dotenv import load_dotenv
from dashscope import Generation
import dashscope
from PyPDF2 import PdfReader
import pandas as pd

# === LOAD ENV ===
load_dotenv()
DASHSCOPE_API_KEY = st.secrets.get("DASHSCOPE_API_KEY") or os.getenv("DASHSCOPE_API_KEY")

# === VALIDATE API KEY ===
if not DASHSCOPE_API_KEY:
    st.error("❌ No API key found. Set it in .env or Streamlit Secrets as 'DASHSCOPE_API_KEY'.")
    st.stop()

# === SET BASE URL ===
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

# === INIT STATE ===
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'username' not in st.session_state:
    st.session_state.username = None

# === UI ===
st.set_page_config(page_title="Chat App", page_icon="🤖")
st.title("🤖 Chat with Memory")
st.markdown("Ask anything")

# === USERNAME FORM ===
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
uploaded_file = st.file_uploader("Upload a file", type=["csv", "xlsx", "pdf", "txt"])

if uploaded_file is not None:
    # Process the file based on its type
    if uploaded_file.type == "application/pdf":
        # If it's a PDF, extract text
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        
        # Append the actual PDF content to chat history (without showing to the user)
        st.session_state.chat_history.append({
            "role": "system",
            "content": f"Here's the content from the uploaded PDF:\n{text}"
        })
    
    elif uploaded_file.type == "text/csv":
        # If it's a CSV, use pandas to extract the data
        df = pd.read_csv(uploaded_file)
        csv_content = df.to_string()  # Convert dataframe to string
        
        # Append the actual CSV content to chat history (without showing to the user)
        st.session_state.chat_history.append({
            "role": "system",
            "content": f"Here's the data from the uploaded CSV:\n{csv_content}"
        })
    
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        # If it's an Excel file (xlsx), use pandas to read it
        df = pd.read_excel(uploaded_file)
        excel_content = df.to_string()  # Convert dataframe to string
        
        # Append the actual Excel content to chat history (without showing to the user)
        st.session_state.chat_history.append({
            "role": "system",
            "content": f"Here's the data from the uploaded Excel file:\n{excel_content}"
        })

    elif uploaded_file.type == "text/plain":
        # If it's a plain text file, read it
        text = uploaded_file.read().decode("utf-8")
        
        # Append the actual text file content to chat history (without showing to the user)
        st.session_state.chat_history.append({
            "role": "system",
            "content": f"Here's the content from the uploaded text file:\n{text}"
        })

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

            # === SAFE CHECK RESPONSE ===
            if response and response.output and hasattr(response.output, "choices"):
                reply = response.output.choices[0].message.content
            else:
                reply = f"⚠️ Gagal dapet balasan dari Dashscope. Cek response: `{response}`"

        except Exception as e:
            reply = f"⚠️ Error pas call Dashscope: {str(e)}"

        # === DISPLAY REPLY ===
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
