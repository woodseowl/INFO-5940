import streamlit as st
from openai import OpenAI
from os import environ

st.title("Share Your Thoughts with a Chatbot")
st.caption("INFO-5940, Assignment 1 - Eric Woods (elw234)")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! How can I help you today?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    client = OpenAI(api_key=environ['OPENAI_API_KEY'])

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(model="openai.gpt-4o",
                                                messages=st.session_state.messages,
                                                stream=True)
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})
