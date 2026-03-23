\# 🛡️ CyberStudy AI - Local RAG Chatbot



A fully local cybersecurity study assistant built with FastAPI, Streamlit, Ollama, and ChromaDB.



\## Features



\- Chat with cybersecurity notes and lab writeups.

\- Multi-document RAG with source-aware answers.

\- Fully local AI using Ollama.

\- FastAPI backend for document ingestion and chat.

\- Streamlit frontend for a simple chat interface.



\## Tech Stack



\- FastAPI

\- Streamlit

\- Ollama

\- ChromaDB

\- Python



\## Demo



Run the backend in one terminal:





uvicorn backend.app.main:app --reload --port 8000

Run the frontend in another terminal:





streamlit run frontend/app.py

Open in your browser:





http://localhost:8501

Screenshots

Streamlit Chat UI

Streamlit Chat



FastAPI Docs

FastAPI Docs



Project Structure

!\[Folder Structure](Folder structure.png)



Architecture



Your Notes (.txt files)

&#x20;       |

&#x20;       v

ChromaDB Vector Store <-> Ollama Embeddings

&#x20;       |

&#x20;       v

FastAPI Backend (/chat)

&#x20;       |

&#x20;       v

Streamlit Frontend (localhost:8501)

Project Structure

cyberstudy-ai/

├── backend/

│   ├── app/

│   │   ├── \_\_init\_\_.py

│   │   └── main.py

│   └── data/

│       ├── chroma/

│       └── docs/

├── frontend/

│   └── app.py

├── .gitignore

├── README.md

└── requirements.txt

Quick Start



git clone https://github.com/plusive27-max/cyberstudy-ai.git

cd cyberstudy-ai

pip install -r requirements.txt

ollama pull llama3.2

ollama pull mxbai-embed-large

uvicorn backend.app.main:app --reload --port 8000

streamlit run frontend/app.py

Example Questions

What is cybersecurity?



What is Wazuh?



How does ransomware work?



What are common cybersecurity threats?



Portfolio Value

Shows full-stack development with FastAPI and Streamlit.



Demonstrates local AI and RAG workflow skills.



Fits a cybersecurity portfolio project well.



Can be extended with PDFs, Docker, and more models.



Future Improvements

Add PDF and DOCX support.



Add chat history.



Add Docker setup.



Add better source formatting.



Add model selection in the UI.



Built by plusive27-max as a cybersecurity and AI portfolio project.

