# 📌 INFO-5940 - Assignment 1
_Eric Woods (elw234), Feb. 2025_

This is an implementation of an AI chatbot that can utilize retrieval augmented generation.


### 1️⃣ Clone the Repository  

Open a terminal and run:  

```bash
git clone https://github.com/woodseowl/INFO-5940.git INFO-5940-elw234 
cd INFO-5940-elw234
git checkout assignment-1
```

### 2️⃣ Set up the OpenAI API Key

```dotenv
# file: .env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.ai.it.cornell.edu/
TZ=America/New_York
```

### 3️⃣ Open in VS Code  

Open in VS Code as a Dev Container


### 4️⃣ Confirm the configuration with a simple chat

Open a terminal to the Dev container and run:  

```bash
streamlit run chat_with_me.py
```

You should be able to chat with the bot at https://localhost:8501


###  5️⃣ Run the Assignment Tasks

Stop the test application and then run the assignment application:

```bash
streamlit run assignment-1.py
```

1. Basic chat requires uploading files on the right, which will be used as the context for the chat.
    - See "File Uploaders" section in `assignment-1.py`
    - The `file_uploader_callback()` manages saving files to disk and triggering generation of embeddings.
2. Multiple files can be uploaded. They are parsed and chunked at the time of upload and stored in the vector database.
    - `ai_utilities.py` contains AI chat, document chunking, and embedding functions
    - Metrics for files in use are displayed below the file uploader
    - Files can be selected and then managed with the buttons and settings below the metrics
3. Once files are uploaded, the chatbot can be used to ask questions about the specific content of the files.
    - By default, the chatbot will use the embeddings to find the most relevant chunks to the question.
    - The chatbot will then use the chunks to generate a response.
    - See `retrieve_rag_chain_result()` in `ai_utilities.py` for embeddings processing
4. The chatbot can also be used to query summary or generalized content of files.
    - By turning off "Query embeddings", the chatbot will generate a response based on all the selected file.
    - See `stream_content_chat()` in `assignment-1.py` for full context processing
5. Settings can be adjusted to address different cases
    - Other settings are available to adjust the behavior of the chatbot and how embeddings are processed.
    - Changing chunk size or overlap requires running "Process Embeddings" to have an effect

---

## Discussion

Achieving a truly useful chatbot for multiple, potentially large files has many complexities in user interface,
content management, and use case requirements. 

Example prompts which worked well with "full context" ("Query embeddings" toggled off):
- "How many files are there?"
- "Summarize the lecture"
- "What was the first topic of the lecture?"
- "What Ivy League schools does Ayham teach at?" (for the cornell, duke, harvard texts)
- "What is Ayham's favorite fruit?"

These become limited if there are too many tokens to send to the AI and in the context of trying to be
efficient with sending tokens. Allowing file selection in that case helps minimize the number of tokens.

Querying the embeddings was not particularly successful in this implementation. The approach was 
too simplistic, simply using the embeddings to retrieve chunks and then generate a response. A different
approach exists in the code (see `stream_embeddings_chat()`) which attempts to implement this algorithm:

   1. Retrieve embeddings in the selected files relevant to the prompt
   2. Determine the source files that match
   3. Generate a response based on the source files and the chat message history

This algorithm has a code issue, but it also fails to get enough context for searching the embeddings,
since the prompt may assume more context is available than is used in the vector store retriever.

### Future work

- Change the `retrieve_rag_chain_result()` to use a contextualized retriever, likely using AI to 
  generate the text for the vector store search.
- Refine methods into libraries for future assignments


## Acknowledgements
- Code was developed in the context of GitHub Copilot line completions and occasional ChatGPT discussions / questions
- I do not have a background in python and have not used Streamlit