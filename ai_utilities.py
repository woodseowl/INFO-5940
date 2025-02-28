from os import environ

import tiktoken
from pypdf import PdfReader

from openai import OpenAI

import chromadb.config
import chromadb.utils.embedding_functions as embedding_functions
from chromadb import ClientAPI

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import MarkdownHeaderTextSplitter

### Setup
storage_path = "/workspace/data/uploaded_files"

embeddings = "text-embedding-3-large"
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=environ['OPENAI_API_KEY'],
    model_name="openai.text-embedding-3-large"
)

openai_client = OpenAI(api_key=environ['OPENAI_API_KEY'])
model = "openai.gpt-4o-mini"

collection_name = "uploaded_files"
chroma_client = chromadb.PersistentClient(
    path=f"{storage_path}/chroma",
    settings=chromadb.config.Settings(allow_reset=True)
)

#########################
# Content processing
#########################

def count_tokens(content):
    encoding = tiktoken.encoding_for_model(embeddings)
    return len(encoding.encode(content))

def chunk_content(file, chunk_size):
    match file["ext"]:
        case "pdf":
            docs = PyPDFLoader(file["path"]).load()
        case _:
            docs = TextLoader(file["path"]).load()

    # TODO - utilize context aware splitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
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
        match file['ext']:
            case "md":
                md_header_splits = md_splitter.split_text(doc.page_content)
                for split in md_header_splits:
                    metadata = doc.metadata.copy()
                    metadata.update(split.metadata)
                    split.metadata = metadata
                docs = md_header_splits
            case _:
                docs = [doc]
    chunks.extend(text_splitter.split_documents(docs))

    return chunks

# def load_documents_from_files(files):
#     loaded_documents = []
#     for file in files:
#         file_path = file["path"]
#         match file["ext"]:
#             case "txt":
#                 doc_loader = TextLoader(file_path)
#             case "pdf":
#                 doc_loader = PyPDFLoader(file_path)
#             case "md":
#                 # doc_loader = UnstructuredMarkdownLoader(file_path)
#                 doc_loader = TextLoader(file_path)
#             case _:
#                 continue
#         loaded_documents.extend(doc_loader.load())
#     return loaded_documents

# def process_documents(selected_file_list, chunk_size):
#     # Entirely empty and reset the database
#     chroma_client.reset()
#     # Create a new collection
#     collection = chroma_client.create_collection(name=collection_name, embedding_function=openai_ef)
#
#     documents = load_documents_from_files(selected_file_list)
#     chunks = chunk_content(documents, chunk_size)
#
#     # Add the documents to the collection
#     collection.add(
#         documents=[doc.page_content for doc in chunks],
#         metadatas=[doc.metadata for doc in chunks],
#         ids=[str(i) for i in range(len(chunks))],
#     )

def generate_embeddings(file, chunk_size=1000):
    chunks = chunk_content(file, chunk_size)

    collection = chroma_client.get_or_create_collection(name=collection_name, embedding_function=openai_ef)

    # TODO: Remove the existing embeddings for the source

    # Add the chunks to the collection
    collection.add(
        documents=[doc.page_content for doc in chunks],
        metadatas=[doc.metadata for doc in chunks],
        ids=[str(i) for i in range(len(chunks))],
    )

def count_embeddings(file):
    # Get the distinct sources for the documents in the collection
    source_count = 0
    if collection_name in [col.name for col in chroma_client.list_collections()]:
        collection = chroma_client.get_collection(collection_name)
        for doc in collection.get()['metadatas']:
            if 'source' in doc and file['path'] == doc['source']:
                source_count+=1
    return source_count

def get_total_embeddings():
    total = 0
    if collection_name in [col.name for col in chroma_client.list_collections()]:
        total = chroma_client.get_collection(collection_name).count()
    return total

def reset_embeddings():
    chroma_client.reset()

#########################
# OpenAI Chat
#########################

def stream_context_chat(chat_messages, context):
    stream = openai_client.chat.completions.create(
        model="openai.gpt-4o",  # Change this to a valid model name
        messages=[
            *chat_messages,
            {"role": "system", "content": f"\n\n---\n\nHere is the context:\n\n{context}"},
        ],
        stream=True
    )
    return stream