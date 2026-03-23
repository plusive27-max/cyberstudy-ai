
# 🛡️ CyberStudy AI - Local RAG Chatbot




A local cybersecurity study assistant built with FastAPI, Streamlit, Ollama, and ChromaDB.

## Features

- Chat with cybersecurity notes and lab writeups
- Multi-document RAG workflow
- Local AI with Ollama
- FastAPI backend
- Streamlit frontend

## Tech Stack

- Python
- FastAPI
- Streamlit
- Ollama
- ChromaDB

## How It Works

1. You add text documents to the project
2. The documents are stored in ChromaDB
3. Ollama creates embeddings and generates answers
4. The FastAPI backend handles requests
5. The Streamlit app provides the chat interface

## Run the Project

Start the backend:


uvicorn backend.app.main:app --reload --port 8000
Start the frontend in another terminal:


streamlit run frontend/app.py
Open:


http://localhost:8501
Quick Start

git clone https://github.com/plusive27-max/cyberstudy-ai.git
cd cyberstudy-ai
pip install -r requirements.txt
ollama pull llama3.2
ollama pull mxbai-embed-large
uvicorn backend.app.main:app --reload --port 8000
streamlit run frontend/app.py

Example Questions:
What is cybersecurity?

What is Wazuh?

How does ransomware work?

What are common cybersecurity threats?

Project Structure

cyberstudy-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   └── data/
│       ├── chroma/
│       └── docs/
├── frontend/
│   └── app.py
├── .gitignore
├── README.md
└── requirements.txt

Future Improvements:
Add PDF and DOCX support

Add chat history

Add Docker setup

Add better source formatting

Add model selection in the UI

Built by plusive27-max.
