from os import environ
import tiktoken
from openai import OpenAI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from pypdf import PdfReader

### Setup
storage_path = "/workspace/data/uploaded_files"

openai_client = OpenAI(api_key=environ['OPENAI_API_KEY'])

embeddings = "text-embedding-3-large"
collection_name = "uploaded_files"
embedding_function = OpenAIEmbeddings(model="openai.text-embedding-3-large")
default_k = 5

#########################
# OpenAI Chat
#########################

def retrieve_context_chat(chat_messages, context, stream=True):
    chat = openai_client.chat.completions.create(
        model="openai.gpt-4o",
        messages=[
            *chat_messages,
            {"role": "system", "content": f"\n\n---\n\nHere is the context:\n\n{context}"},
        ],
        stream=stream
    )
    return chat

def retrieve_embeddings_chat(prompt, chat_messages, files, k=default_k):

    vector_store = _get_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": k,
           #"where": {"source": files[0]["path"]},
        })

    # Find the most relevant documents by determining the metadata sources from the retriever
    results = retriever.invoke(prompt)
    #print(*results)

    source_files = [doc.metadata["source"] for doc in results]

    context = ""
    for file in source_files:
        content = get_file_content(file)
        context += f"### {file}\n\n{content}\n\n"

    return retrieve_context_chat(chat_messages, context)


def retrieve_rag_chain_result(prompt, k):
    vector_store = _get_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": k,
            #"where": {"source": files[0]["path"]},
        })

    llm = ChatOpenAI(model="openai.gpt-4o")

    rag_chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | _get_embeddings_prompt()
        | llm
        | StrOutputParser()
    )
    return rag_chain.invoke(prompt)



#########################
# Content processing
#########################

def get_file_content(source):
    extension= source.split('.')[-1],
    match extension:
        case "pdf":
            with open(source, "rb") as f:
                pdf_reader = PdfReader(f)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
        case _:
            with open(source, "r", encoding="utf-8") as f:
                content = f.read()
    return content

def count_tokens(content):
    encoding = tiktoken.encoding_for_model(embeddings)
    return len(encoding.encode(content))

def _chunk_content(file, chunk_size, chunk_overlap):
    match file["ext"]:
        case "pdf":
            docs = PyPDFLoader(file["path"]).load()
        case _:
            docs = TextLoader(file["path"]).load()

    # TODO - utilize context aware splitter?
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    return text_splitter.split_documents(docs)

    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
        ],
        return_each_line=False,
        strip_headers=False
    )

    chunks = []
    for doc in docs:
        split_docs = [doc]
        match file['ext']:
            case "md":
                md_header_splits = md_splitter.split_text(doc.page_content)
                for split in md_header_splits:
                    metadata = doc.metadata.copy()
                    metadata.update(split.metadata)
                    split.metadata = metadata
                split_docs = md_header_splits
        chunks.extend(text_splitter.split_documents(split_docs))

    return chunks

#########################
# Manage embeddings
#########################

def _get_vector_store():
    return Chroma(
        collection_name=collection_name,
        embedding_function=embedding_function,
        persist_directory=f"{storage_path}/chroma",
    )

def generate_embeddings(file, chunk_size=100, chunk_overlap=0):
    chunks = _chunk_content(file, chunk_size, chunk_overlap)

    # Do not add the same file multiple times, just replace the embeddings
    remove_embeddings(file)

    vector_store = _get_vector_store()
    vector_store.add_documents(chunks)

def count_embeddings(file=None):
    # Get the distinct sources for the documents in the collection
    vector_store = _get_vector_store()
    if file:
        results = vector_store.get(
            where={"source": file["path"]},
            include=["metadatas"]
        )
    else:
        results = vector_store.get(include=["metadatas"])
    return len(results["ids"])

def get_total_embeddings():
    vector_store = _get_vector_store()
    results = vector_store.get(include=["metadatas"])
    return len(results["ids"])

def remove_embeddings(file=None):
    vector_store = _get_vector_store()
    if file:
        results = vector_store.get(
            where={"source": file["path"]},
            include=["metadatas"]
        )
        if len(results["ids"]) > 0:
            vector_store.delete(results["ids"])
    else:
        vector_store.reset_collection()


#########################
# Query embeddings
#########################

def _get_embeddings_prompt():
    template = """
        You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
        If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.

        Question: {question} 

        Context: {context} 

        Answer:
    """
    return PromptTemplate.from_template(template)

def _format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

def query_embeddings(question, k):
    vector_store = _get_vector_store()
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})
    prompt_chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | _get_embeddings_prompt()
    )