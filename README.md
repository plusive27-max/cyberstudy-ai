 # 🛡️ CyberStudy AI

<image-card alt="Python" src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" ></image-card>
<image-card alt="FastAPI" src="https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi" ></image-card>
<image-card alt="Streamlit" src="https://img.shields.io/badge/Streamlit-frontend-FF4B4B?logo=streamlit" ></image-card>
<image-card alt="Ollama" src="https://img.shields.io/badge/Ollama-local%20LLM-black" ></image-card>
<image-card alt="ChromaDB" src="https://img.shields.io/badge/ChromaDB-vector%20store-orange" ></image-card>
<image-card alt="Docker" src="https://img.shields.io/badge/Docker-compose-2496ED?logo=docker" ></image-card>

A **fully local** RAG (Retrieval-Augmented Generation) chatbot for studying cybersecurity.  
Upload your notes, writeups, or study guides — then ask questions and get answers grounded in your own documents.  
No cloud APIs, no data leaving your machine.

---

## ✨ Features

- 💬 **Persistent chat history** — conversation stays on screen as you continue asking
- 📄 **Multi-format document support** — `.txt`, `.pdf`, and `.docx`
- 🔍 **RAG pipeline** — answers are grounded in your uploaded documents with source citations
- 🔒 **Fully local** — powered by Ollama; nothing is sent to external servers
- 🐳 **Docker support** — spin up the entire stack with one command
- 📂 **Document manager** — upload, list, and clear your knowledge base from the sidebar

---

## 🏗️ Architecture

┌─────────────────────┐        HTTP        ┌──────────────────────┐
│  Streamlit Frontend │  ──────────────▶  │  FastAPI Backend     │
│  (Chat UI + Upload) │                   │  (RAG pipeline)      │
└─────────────────────┘                   └──────────┬───────────┘
│
┌──────────────────────┼────────────┐
▼                       ▼            ▼
ChromaDB              OllamaEmbeddings  ChatOllama
(vector store)         (mxbai-embed-large) (llama3.2)




---

## 🚀 Quick Start

### Option A — Docker (recommended)

> Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker + Docker Compose.

```bash
git clone https://github.com/plusive27-max/cyberstudy-ai.git
cd cyberstudy-ai

# Start everything (Ollama + backend + frontend)
docker compose up --build

On first run, pull the required Ollama models:
docker exec -it cyberstudy-ollama ollama pull llama3.2
docker exec -it cyberstudy-ollama ollama pull mxbai-embed-large

Then open http://localhost:8501 in your browser.
No GPU? Remove the deploy block from docker-compose.yml before running.


🪟 How to Run on Windows (Docker Desktop)
Tested on Windows 10/11 + Docker Desktop + WSL2.
Step-by-step:

1. Install Docker Desktop (if not already installed)
→ Download from docker.com
→ Enable WSL 2 during installation
2. Clone and prepare
PowerShell:
git clone https://github.com/plusive27-max/cyberstudy-ai.git
cd cyberstudy-ai
cp .env.example .env

3. Edit .env (use Notepad or VS Code)
Change the API_KEY to something long and random.

4. Start the app

PowerShell:
docker compose down
docker compose up --build

5. Open http://localhost:8501 in your browser


Common Windows fixes:

If docker command not found → restart Docker Desktop completely
If ChromaDB error appears → delete the folder backend\data\chroma and restart
Want GPU later? → Uncomment the NVIDIA block in docker-compose.yml after installing NVIDIA Container Toolkit


Option B — Manual (local Python)
Prerequisites: Python 3.11+, Ollama installed and running

Bash:

git clone https://github.com/plusive27-max/cyberstudy-ai.git
cd cyberstudy-ai

# Install dependencies
pip install -r requirements.txt

# Pull Ollama models
ollama pull llama3.2
ollama pull mxbai-embed-large

# Start the backend (terminal 1)
uvicorn backend.app.main:app --reload --port 8000

# Start the frontend (terminal 2)
streamlit run frontend/app.py

Open http://localhost:8501.

📖 Usage

1.Upload documents — use the sidebar to upload .txt, .pdf, or .docx files
2.Ask questions — type in the chat box; the assistant answers using your documents
3.Check sources — expand the "📎 Sources" section under each answer to see which files were used
4.Clear & reset — use the sidebar buttons to clear chat history or wipe the knowledge base


📁 Project Structure

cyberstudy-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI app + RAG pipeline
│   └── data/
│       ├── docs/            # Your uploaded documents go here
│       └── chroma/          # ChromaDB vector store (auto-generated)
├── frontend/
│   └── app.py               # Streamlit chat UI
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── requirements.txt
└── README.md



🔧 Configuration
All settings can be overridden with environment variables (useful in Docker or .env files):

Variable,Default,Description
LLM_MODEL,llama3.2,Ollama model for answering
EMBED_MODEL,mxbai-embed-large,Ollama model for embeddings
DATA_PATH,backend/data/docs,Where uploaded documents live
DB_PATH,backend/data/chroma,Where ChromaDB persists
BACKEND_URL,http://localhost:8000,Frontend → backend URL


🗺️ Roadmap

 Streaming responses (token-by-token output)
 Multi-turn conversation context in the RAG chain
 Model selection from the UI
 Better source formatting (page numbers, highlights)
 User authentication


 🛠️ Tech Stack

Frontend -  Streamlit
Backend  -  FastAPI
LLM   -   Ollama (llama3.2)
Embeddings  -  Ollama (mxbai-embed-large)
Vector DB   -   ChromaDB
RAG   -  LangChain
Containers  -  Docker + Docker Compose


Built by plusive27-max