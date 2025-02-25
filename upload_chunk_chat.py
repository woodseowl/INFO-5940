import streamlit as st
from openai import OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import os
from os import environ
import tiktoken
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

storage_path = "/workspace/data/uploaded_files"
os.makedirs(storage_path, exist_ok=True)
openai_client = OpenAI(api_key=environ['OPENAI_API_KEY'])
model = "openai.gpt-4o-mini"
embeddings = "openai.text-embedding-3-large"
documents = []

st.title("File Upload with Chunking")
st.caption("INFO-5940, Assignment 1, part 2 - Eric Woods (elw234)")

st.chat_message("assistant").write("Hello! Please upload a file to begin.")

uploaded_files = st.file_uploader("Upload text files", type=(["txt","md","pdf"]), accept_multiple_files=True)

def upload_files(uploaded_files):
    documents = []
    for uploaded_file in uploaded_files:
        file_path = f"{storage_path}/{uploaded_file.name}"
        with open(file_path, "w") as file:
            file_content = uploaded_file.read().decode("utf-8")
            file.write(file_content)
        extension = uploaded_file.name.split('.')[-1]
        match extension:
            # case "md":
            #     doc_loader = UnstructuredMarkdownLoader(file_path)
            case "pdf":
                doc_loader = PyPDFLoader(file_path)
            case _:
                doc_loader = TextLoader(file_path)

        documents.extend(doc_loader.load())
    return documents

def summarize_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()
    response = openai_client.chat.completions.create(model=model, messages=[
        {"role": "system", "content": "Please summarize the content as briefly as possible into bulleted points."},
        {"role": "user", "content": content}
    ])
    return response.choices[0].message.content

def count_tokens(content):
    encoding = tiktoken.encoding_for_model("gpt-4")
    return len(encoding.encode(content))

def chunk_content(content, chunk_size=1000):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
    return text_splitter.split_documents(content)

def process_documents():
    #chromadb.Client().delete_collection("uploaded_files")
    chunks = chunk_content(documents)
    vectorstore = Chroma.from_documents(
        documents = chunks, 
        embedding = OpenAIEmbeddings(model=embeddings), 
        persist_directory = f"{storage_path}/chroma",
        collection_name = "uploaded_files",
    )
    st.sidebar.success(f"Processed {len(documents)} document(s) into {len(chunks)} chunks.")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_answer_from_context(question):
    llm = ChatOpenAI(
        model="openai.gpt-4o",
        temperature=0.2,
    )
    kb_template = """
        You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
        If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
        
        Question: {question} 
        
        Context: {context} 
        
        Answer:
    """
    kb_prompt = PromptTemplate.from_template(kb_template)
    vectorstore = Chroma(
        embedding_function = OpenAIEmbeddings(model=embeddings),
        persist_directory = f"{storage_path}/chroma",
        collection_name = "uploaded_files"
    )
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | kb_prompt
        | llm
        | StrOutputParser()
    )
    response = rag_chain.invoke(question)
    return response


if uploaded_files:
    documents = upload_files(uploaded_files)
    tokens_found = 0
    word_count = 0
    info = []
    for doc in documents:
        doc_words = len(doc.page_content.split())
        word_count += doc_words
        tokens_found += count_tokens(doc.page_content)
        file_name = os.path.basename(doc.metadata['source'])
        info.append(f"- {file_name} ({doc_words} words)\n")
    st.info(f"Uploaded {len(documents)} file{'s' if len(documents) > 1 else ''}.")

    st.sidebar.header("Files in use")
    st.sidebar.markdown("".join(info))

    # Show a button to process the files
    st.sidebar.button("Process Files", on_click=lambda: process_documents())

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
        st.session_state.messages.append({"role": "assistant", "content": f"What would you like to know about these files?"})
    else:
        # Remove any system messages from the previous run
        st.session_state.messages = [msg for msg in st.session_state.messages if msg["role"] != "system"]

    for msg in st.session_state.messages:
        if msg["role"] != "system": st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            answer = get_answer_from_context(prompt)
            response = st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": response})
