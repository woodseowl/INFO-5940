import chromadb.config
import streamlit as st
from openai import OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import os
from os import environ
import tiktoken
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from chromadb import ClientAPI
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
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=environ['OPENAI_API_KEY'], 
    model_name=embeddings
)
chroma_client = chromadb.PersistentClient(
    path=f"{storage_path}/chroma",
    settings=chromadb.config.Settings(allow_reset=True)
)

st.title("File Upload with Chunking")
st.caption("INFO-5940, Assignment 1, part 2 - Eric Woods (elw234)")

# Manage streamlit file_uploader content
# (see https://discuss.streamlit.io/t/clear-the-file-uploader-after-using-the-file-data/66178/4)
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def summarize_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()
    response = openai_client.chat.completions.create(model=model, messages=[
        {"role": "system", "content": "Please summarize the content into a very brief outline."},
        {"role": "user", "content": content}
    ])
    return response.choices[0].message.content

def count_tokens(content):
    encoding = tiktoken.encoding_for_model("gpt-4")
    return len(encoding.encode(content))

def chunk_content(content, chunk_size=1000):
    # TODO - make chunk size a user input
    # TODO - make chunk overlap a user input
    # TODO - utilize context aware splitter
    # TODO - store initial document in the metadata so it can be filtered
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
    return text_splitter.split_documents(content)

def process_documents(client: ClientAPI, documents):
    # TODO - Only process changes
    # Entirely empty and reset the database
    client.reset()
    # Create a new collection
    collection = client.create_collection(name="uploaded_files", embedding_function=openai_ef)

    # Get the selected documents from the sidebar
    selected_documents = []
    for doc in documents:
        file_name = os.path.basename(doc.metadata['source'])
        if st.session_state.get(file_name, False):
            selected_documents.append(doc)
    
    # Chunk the documents
    chunks = chunk_content(selected_documents)

    # Add the documents to the collection
    collection.add(
        documents=[doc.page_content for doc in chunks],
        metadatas=[doc.metadata for doc in chunks],
        ids=[str(i) for i in range(len(chunks))],
    )

    tokens_count = sum([count_tokens(doc.page_content) for doc in chunks])

    st.sidebar.success(f"Processed {len(selected_documents)} document(s) with {tokens_count:,} tokens into {collection.count()} embeddings.")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_answer_from_context(client, question):
    kb_template = """
        You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
        If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
        
        Question: {question} 
        
        Context: {context} 
        
        Answer:
    """

    # TODO - Filter embeddings to only search in selected documents
    vectorstore = Chroma(
        collection_name="uploaded_files",
        embedding_function=OpenAIEmbeddings(model=embeddings),
        persist_directory=f"{storage_path}/chroma",
        client=client,
    )
    
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | PromptTemplate.from_template(kb_template)
        | ChatOpenAI(model="openai.gpt-4o", temperature=0.2)
        | StrOutputParser()
    )
    return rag_chain.invoke(question)

def get_parseable_documents_from_dir():
    # Filter files with txt, pdf, and md extensions
    parseable_files = [file for file in os.listdir(storage_path) if file.endswith(('.txt', '.pdf', '.md'))]
    parseable_files.sort()
    return parseable_files

def load_documents_from_files(files):
    loaded_documents = []
    for file in files:
        file_path = os.path.join(storage_path, file)
        if os.path.isfile(file_path):
            extension = file.split('.')[-1]
            match extension:
                case "txt":
                    doc_loader = TextLoader(file_path)
                case "pdf":
                    doc_loader = PyPDFLoader(file_path)
                case "md":
                    # doc_loader = UnstructuredMarkdownLoader(file_path)
                    doc_loader = TextLoader(file_path)
                case _:
                    continue
            loaded_documents.extend(doc_loader.load())
    return loaded_documents

def show_files_in_use(documents):
    tokens_found = 0
    word_count = 0
    # If no documents are found, show a message
    if not documents:
        st.sidebar.write(f"No files found in {storage_path}")
    for doc in documents:
        doc_words = len(doc.page_content.split())
        doc_tokens = count_tokens(doc.page_content)
        word_count += doc_words
        tokens_found += doc_tokens
        file_name = os.path.basename(doc.metadata['source'])
        st.sidebar.checkbox(
            f"- {file_name} ({doc_tokens // 100 * 100:,} tokens)", 
            value=True, key=file_name, 
        )

def remove_documents(client: ClientAPI, files):
    # Remove the files from the storage directory
    for file in files:
        file_path = os.path.join(storage_path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    # Reset the uploader
    st.session_state.uploaded_files = []
    # Entirely empty and reset the database
    client.reset()
    st.rerun()

def show_metrics(documents):
    # TODO - Show metrics for the uploaded files
    st.sidebar.header("Metrics")
    # Tokens selected
    tokens_selected = 0
    for doc in documents:
        file_name = os.path.basename(doc.metadata['source'])
        if st.session_state.get(file_name, False):
            tokens_selected += count_tokens(doc.page_content)
    st.sidebar.metric("Tokens selected: ", f"{tokens_selected // 100 * 100:,}")
    # Embeddings count in the database
    st.sidebar.metric("Embeddings: ", chroma_client.get_collection("uploaded_files").count())
    st.sidebar.metric("Chunk size: ", 1000)

def upload_files():
    files_uploaded = st.session_state[f"uploaded_files_{st.session_state.uploader_key}"]
    for uploaded_file in files_uploaded:
        with open(f"{storage_path}/{uploaded_file.name}", "w") as file:
            file.write(uploaded_file.read().decode("utf-8"))
    st.session_state.uploader_key += 1
    st.sidebar.info(f"Uploaded {len(files_uploaded)} file{'s' if len(files_uploaded) != 1 else ''}.")


######################
# User interface
######################

file_names = get_parseable_documents_from_dir()
documents = load_documents_from_files(file_names)

######################
# Sidebar
######################

st.sidebar.header("Files in Use")
show_files_in_use(documents)

uploaded_files = st.sidebar.file_uploader(
    "Upload text files", 
    type=(["txt","md","pdf"]), 
    accept_multiple_files=True,
    label_visibility="collapsed",
    key=f"uploaded_files_{st.session_state.uploader_key}",
    on_change=lambda: upload_files()
)

if documents:
    # Show a button to process the files
    if st.sidebar.button("Process Files", icon="⚙️"):
        process_documents(chroma_client, documents)

    if st.sidebar.button("Clear Files", icon="❌"):
        remove_documents(chroma_client, file_names)

    show_metrics(documents)

########################
# Chat interface
########################⚙️

# Show a message if no files are uploaded
if not documents:
    st.chat_message("assistant").write("Hello! Please upload a file to begin.")
else:
    if "messages" not in st.session_state:
        st.session_state.messages = []
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
            answer = get_answer_from_context(chroma_client, prompt)
            st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    if st.button("Clear Chat", icon="❌"):
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": f"What would you like to know about these files?"})
        st.rerun()