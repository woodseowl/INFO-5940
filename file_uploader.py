import streamlit as st
import os
from millify import millify

import tiktoken
from pypdf import PdfReader

### Setup
supported_file_types = ('.txt', '.pdf', '.md')
text_file_types = ('.txt', '.md')
storage_path = "/workspace/data/uploaded_files"
os.makedirs(storage_path, exist_ok=True)
embeddings = "text-embedding-3-large"

#########################
# Content processing
#########################

def count_tokens(file):
    match file["ext"]:
        case "pdf":
            with open(file["path"], "rb") as f:
                pdf_reader = PdfReader(f)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
        case _:
            with open(file["path"], "r", encoding="utf-8") as f:
                content = f.read()
    encoding = tiktoken.encoding_for_model(embeddings)
    return len(encoding.encode(content))


#########################
# File Uploader
#########################

### Setup
# Manage streamlit file_uploader content
# (see https://discuss.streamlit.io/t/clear-the-file-uploader-after-using-the-file-data/66178/4)
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

### Supporting functions

def load_file_list():
    # Return a list of files in the storage directory that are supported_file_types.
    file_list = []
    filtered_files = [f for f in os.listdir(storage_path) if f.endswith(supported_file_types)]
    for file_name in filtered_files:
        file_path = os.path.join(storage_path, file_name)
        metadata = {
            "name": file_name,
            "path": file_path,
            "ext": file_path.split('.')[-1],
            "size": os.path.getsize(file_path),
        }
        metadata["tokens"] = count_tokens(metadata)
        file_list.append(metadata)
    return file_list

def refresh_file_list():
    st.session_state.file_list = load_file_list()

def get_file_list():    
    if 'file_list' not in st.session_state:
        refresh_file_list()
    return st.session_state.file_list

def display_files_in_use(placeholder):
    current_files = get_file_list()
    with placeholder.container():
        if current_files:
            for file in current_files:
                st.checkbox(file["name"], key=f"file_checkbox_{file['path']}")
        else:
            st.write("No files in directory.")

def get_selected_file_list():
    selected_files = []
    for file in get_file_list():
        if st.session_state.get(f"file_checkbox_{file['path']}", False):
            selected_files.append(file)
    return selected_files

def file_uploader_callback():
    uploaded_files = st.session_state[f"file_uploader_{st.session_state.uploader_key}"]
    # Handle the uploaded files
    for uploaded_file in uploaded_files:
        # Save the file to the storage directory
        file_path = os.path.join(storage_path, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    # Clear the file uploader + refresh the file list
    st.session_state.uploader_key += 1
    refresh_file_list()

def remove_files_callback():
    for file in get_selected_file_list():
        os.remove(file["path"])
    # Refresh the file list
    refresh_file_list()

#########################
# Chat Helpers
#########################
def chat_started():
    return "messages" in st.session_state and len(st.session_state.messages) > 0

def get_chat_history():
    if chat_started():
        return st.session_state.messages
    else:
        return []

def add_chat_message(role, content):
    message = {"role": role, "content": content}
    if not chat_started():
        st.session_state.messages = [message]
    else:
        st.session_state.messages.append(message)

def clear_chat():
    st.session_state.messages = []
    
#########################
# Page Layout
#########################

st.set_page_config(layout="wide")
st.title("File Uploader Example")

current_files = get_file_list()
selected_files = get_selected_file_list()

left, right = st.columns([3,2])

with left:
    #########################
    ### Chat
    #########################

    chat_box = st.container()

    if not chat_started():
        if not current_files:
            with chat_box.chat_message("assistant"):
                    st.write("To begin, upload some files.")
        else:
            add_chat_message("assistant", "Hello! You can ask me questions about the files you upload.")
        
    for message in get_chat_history():
        with chat_box.chat_message(message["role"]):
            st.markdown(message["content"])

    if current_files:
        st.caption(f"There are {len(current_files)} files available for discussion. You have selected {len(selected_files)} of them.")

        if prompt := st.chat_input("Ask a question about the files in use."):
            add_chat_message("user", prompt)
            with chat_box.chat_message("user"):
                st.write(prompt)
            # Simulate a response from the assistant
            response = f"Simulated response to: {prompt}"
            add_chat_message("assistant", response)
            with chat_box.chat_message("assistant"):
                st.markdown(response)

    if current_files: st.button(
        "Clear Chat",
        icon="❌",
        on_click=lambda: clear_chat(),
        disabled=not chat_started()
    )


with right:
    #########################
    ### File Uploader
    #########################
    st.subheader("Files in Use")
    if current_files:
        for file in current_files:
            st.checkbox(
                f'{file["name"]} ({millify(file["tokens"], precision=1)} tokens)', 
                key=f"file_checkbox_{file['path']}"
            )
    else:
        st.write("No files in directory.")

    st.file_uploader(
        "Upload files", 
        type=supported_file_types, 
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"file_uploader_{st.session_state.uploader_key}",
        on_change=lambda: file_uploader_callback()
    )

    # If there are files in use, show a button to clear files
    if get_file_list():
        selected_files = get_selected_file_list()
        st.button(
            f"Remove {len(selected_files)} Files", 
            icon="❌",
            on_click=lambda: remove_files_callback(),
            disabled=not bool(selected_files)
        )

    st.divider()
    
    #########################
    ### Metrics
    #########################
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Documents",
            value=len(get_file_list()),
            border=True
        )

    with col2:
        st.metric(
            label="Tokens",
            value=millify(sum([file["tokens"] for file in get_file_list()]), precision=1),
            border=True
        )