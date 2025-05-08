import streamlit as st
import os
from dotenv import load_dotenv
from dashscope import Generation
import dashscope
import pandas as pd
import openpyxl
import PyPDF2
import io

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
        name = st.text_input("Enter your name motherfucker:", placeholder="Contoh: Nigger")
        submitted = st.form_submit_button("Start Chat")
        if submitted and name:
            st.session_state.username = name
            st.rerun()
        else:
            st.stop()

# === FILE UPLOAD ===
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "pdf", "txt"])

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1].lower()  # Get file extension

    # === HANDLE CSV FILE ===
    if file_type == "csv":
        try:
            st.write("Reading CSV file...")
            df = pd.read_csv(uploaded_file)
            if df.empty:
                st.error("⚠️ CSV file is empty!")
            else:
                st.write(df.head())  # Show the first few rows of the dataframe
        except Exception as e:
            st.error(f"⚠️ Error reading CSV file: {e}")

    # === HANDLE XLSX FILE ===
    elif file_type == "xlsx":
        try:
            st.write("Reading Excel file...")
            wb = openpyxl.load_workbook(uploaded_file)
            sheet = wb.active
            data = sheet.values
            df = pd.DataFrame(data)
            if df.empty:
                st.error("⚠️ Excel file is empty!")
            else:
                st.write(df.head())  # Show the first few rows of the data
        except Exception as e:
            st.error(f"⚠️ Error reading Excel file: {e}")

    # === HANDLE PDF FILE ===
    elif file_type == "pdf":
        try:
            st.write("Reading PDF file...")
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            if len(pdf_reader.pages) == 0:
                st.error("⚠️ PDF is empty!")
            else:
                for page in pdf_reader.pages:
                    text += page.extract_text()
                if not text.strip():
                    st.error("⚠️ No readable text found in PDF!")
                else:
                    st.text(text)  # Show extracted text from the PDF
        except Exception as e:
            st.error(f"⚠️ Error reading PDF file: {e}")

    # === HANDLE TXT FILE ===
    elif file_type == "txt":
        try:
            st.write("Reading Text file...")
            text = uploaded_file.getvalue().decode("utf-8")
            if not text.strip():
                st.error("⚠️ Text file is empty!")
            else:
                st.write(text)  # Show text content of the file
        except Exception as e:
            st.error(f"⚠️ Error reading Text file: {e}")

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
user_input = st.chat_input("What's on your mind vro...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Im thinking, be patient bitch..."):
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
