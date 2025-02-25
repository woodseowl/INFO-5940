# 📌 INFO-5940 - Assignment 1
_Eric Woods (elw234), Feb. 2025_

This is an implementation of an AI chatbot that can utilize retrieval augmented generation.

---

## 🛠️ Prerequisites  

Before starting, ensure you have the following installed on your system:  

- [Docker](https://www.docker.com/get-started) (Ensure Docker Desktop is running)  
- [VS Code](https://code.visualstudio.com/)  
- [VS Code Remote - Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)  
- [Git](https://git-scm.com/)  
- OpenAI API Key

---

## 🚀 Setup Guide  

### 1️⃣ Clone the Repository  

Open a terminal and run:  

```bash
git clone https://github.com/woodseowl/INFO-5940.git INFO-5940-elw234 
cd INFO-5940-elw234
git checkout assignment-1
```

---

### 2️⃣ Set up the OpenAI API Key

1. Inside the project folder, create a `.env` file:  

   ```bash
   touch .env
   ```

2. Add your API key and base URL:  

   ```plaintext
   OPENAI_API_KEY=your-api-key-here
   OPENAI_BASE_URL=https://api.ai.it.cornell.edu/
   TZ=America/New_York
   ```

---

### 3️⃣ Open in VS Code with Docker  

1. Open **VS Code**, navigate to the `INFO-5940-elw234` folder.  
2. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on Mac) and search for:  
   ```
   Remote-Containers: Reopen in Container
   ```
3. Select this option. VS Code will build and open the project inside the container.  

📌 **Note:** If you don’t see this option, ensure that the **Remote - Containers** extension is installed.  

---

### 4️⃣ Confirm the configuration with a simple chat

1. Open a terminal in VS Code and run:  

   ```bash
   streamlit run chat_with_me.py
   ```

---

## ✅ Assignment Tasks

1. Utilize the Provided Docker and Devcontainer Setup
  - [x] **Task 1:** Use the provided template with Docker and .devcontainer configurations for your application development.
  - [x] **Task 2:** Ensure your application runs successfully within this environment. (See chat_with_me.py)

2. File Upload Functionality for .txt Files
  - [x] **Task 1:** A user interface component that enables file selection and uploading.
  - [x] **Task 2:** Backend handling of multiple uploaded .txt files. (See upload_txt.py)

3. Conversational Interface with Document Content
  - [x] **Task 1:** Implement a conversational interface with the uploaded document content. (See upload_chat.py)
  - [x] **Task 2:** Efficiently handle large documents by chunking them into smaller, manageable pieces.

## 🏃 Running Jupyter Notebook From Outside VS Code

Once inside the **VS Code Dev Container**, you should be able to run the notebooks from the IDE but you can also launch the Jupyter Notebook server:  

```bash
jupyter notebook --ip 0.0.0.0 --port=8888 --no-browser --allow-root
```

---

### Access Jupyter Notebook  

When the notebook starts, it will output a URL like this:  

```
http://127.0.0.1:8888/?token=your_token_here
```

Copy and paste this link into your browser to access the Jupyter Notebook interface.  

---

## 🛠️ Troubleshooting  

### **Container Fails to Start?**  
- Ensure **Docker Desktop is running**.  
- Run `docker-compose up --build` again.  
- If errors persist, delete existing containers with:  

  ```bash
  docker-compose down
  ```

  Then restart:  

  ```bash
  docker-compose up --build
  ```

### **Cannot Access Jupyter Notebook from outside VS Code?**  
- Ensure you’re using the correct port (`8888`).  
- Run `docker ps` to check if the container is running.  

### **OpenAI API Key Not Recognized?**  
- Check if `.env` is correctly created.  
- Ensure `docker-compose.yml` includes `env_file: - .env`.  
- Restart the container after making changes (`docker-compose up --build`).  
