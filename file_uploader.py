import streamlit as st
import os

### Setup
supported_file_types = ('.txt', '.pdf', '.md')
storage_path = "/workspace/data/uploaded_files"
os.makedirs(storage_path, exist_ok=True)


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
        file_list.append({
            "name": file_name,
            "path": file_path,
            "size": os.path.getsize(file_path),
        })
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

def clear_files_callback():
    for file in get_selected_file_list():
        os.remove(file["path"])
    # Refresh the file list
    refresh_file_list()


#########################
# Page Layout
#########################

st.set_page_config(layout="wide")
st.title("File Uploader Example")

left, right = st.columns(2)

with left:
    st.write("Upload a file.")

with right:
    st.subheader("Files in Use")
    current_files = get_file_list()
    if current_files:
        for file in current_files:
            st.checkbox(file["name"], key=f"file_checkbox_{file['path']}")
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
        st.button(
            "Clear Files", 
            icon="❌",
            on_click=lambda: clear_files_callback(),
            disabled=not bool(get_file_list())
        )
