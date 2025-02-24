import streamlit as st
from openai import OpenAI
import os
from os import environ

file_path = "/workspace/data/uploaded_files"
os.makedirs(file_path, exist_ok=True)
client = OpenAI(api_key=environ['OPENAI_API_KEY'])
model = "openai.gpt-4o-mini"

st.title("File Upload")
st.caption("INFO-5940, Assignment 1, part 2 - Eric Woods (elw234)")

st.chat_message("assistant").write("Hello! Please upload a .txt file to begin.")

uploaded_files = st.file_uploader("Upload .txt files", type=("txt"), accept_multiple_files=True)

def upload_files(uploaded_files):
    file_details = []
    for uploaded_file in uploaded_files:
        file_content = uploaded_file.read().decode("utf-8")
        file_details.append({"name": uploaded_file.name, "words": len(file_content.split())})
        with open(f"{file_path}/{uploaded_file.name}", "w") as file:
            file.write(file_content)
    return file_details

def summarize_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()
    # Use the GPT-4o model to summarize the content of the file
    response = client.chat.completions.create(model=model, messages=[
        {"role": "system", "content": "Please summarize the content as briefly as possible into bulleted points."},
        {"role": "user", "content": content}
    ])
    return response.choices[0].message.content

if uploaded_files:
    file_details = upload_files(uploaded_files)
    message = f"Uploaded {len(file_details)} file{'s' if len(file_details) > 1 else ''}.\n" \
              f"Total word count: {sum([file['words'] for file in file_details])}"
    st.info(message)

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
        st.session_state.messages.append({"role": "assistant", "content": f"What would you like to know about these files?"})
    else:
        # Remove any system messages from the previous run
        st.session_state.messages = [msg for msg in st.session_state.messages if msg["role"] != "system"]

    for file in file_details:
        with open(f"{file_path}/{file['name']}", "r") as file_content:
            content = file_content.read()
        st.session_state["messages"].append({"role": "system", "content": f"Here's the content of {file['name']}:\n\n{content}"})

    for msg in st.session_state.messages:
        if msg["role"] != "system": st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(model=model,
                                                    messages=st.session_state.messages,
                                                    stream=True)
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
