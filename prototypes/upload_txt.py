import streamlit as st
import os

file_path = "/workspace/data/uploaded_files"
os.makedirs(file_path, exist_ok=True)

st.title("File Upload")
st.caption("INFO-5940, Assignment 1, part 2 - Eric Woods (elw234)")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! Please upload a .txt file to begin."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

uploaded_files = st.file_uploader("Upload .txt files", type=("txt"), accept_multiple_files=True)
if uploaded_files:
    file_details = []
    for uploaded_file in uploaded_files:
        file_content = uploaded_file.read().decode("utf-8")
        file_details.append({"name": uploaded_file.name, "words": len(file_content.split())})
        with open(f"{file_path}/{uploaded_file.name}", "w") as file:
            file.write(file_content)

    message = f"Uploaded {len(file_details)} file{'s' if len(file_details) > 1 else ''}. Total word count: {sum([file['words'] for file in file_details])}"
    st.chat_message("assistant").write(message)
