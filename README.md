\# 🛡️ CyberStudy AI - Local RAG Chatbot



\*\*Fully local cybersecurity study assistant\*\* built in 5 days using FastAPI + Streamlit + Ollama + ChromaDB.



\[!\[FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge\&logo=fastapi)](https://fastapi.tiangolo.com)

\[!\[Streamlit](https://img.shields.io/badge/Streamlit-FE6F4F?style=for-the-badge\&logo=streamlit)](https://streamlit.io)

\[!\[Ollama](https://img.shields.io/badge/Ollama-1B1B1D?style=for-the-badge\&logo=ollama)](https://ollama.com)

\[!\[ChromaDB](https://img.shields.io/badge/ChromaDB-FF3B30?style=for-the-badge\&logo=chroma)](https://www.trychroma.com)



\## 🚀 Features

\- 💬 Chat with cybersecurity notes and lab writeups.

\- 📚 Multi-document RAG with source citations.

\- 🧠 Local AI using llama3.2 and mxbai-embed-large.

\- 📁 Upload new TXT documents through the API.

\- 🎨 Clean Streamlit UI with a FastAPI backend.



\## 🎯 Live Demo

Run the backend in one terminal:





uvicorn backend.app.main:app --reload --port 8000

Run the frontend in a second terminal:



streamlit run frontend/app.py

Then open:





http://localhost:8501

📸 Screenshots

Streamlit Chat UI



Streamlit Chat



FastAPI Backend Docs



FastAPI Docs



Project Structure



!\[Folder Structure](Folder structure.png)



🏗️ Architecture

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

📂 Project Structure



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





\## ⚡ Quick Start





git clone https://github.com/plusive27-max/cyberstudy-ai.git

cd cyberstudy-ai

pip install -r requirements.txt

ollama pull llama3.2

ollama pull mxbai-embed-large

uvicorn backend.app.main:app --reload --port 8000

streamlit run frontend/app.py





🧠 Example Questions

What is cybersecurity?



What is Wazuh?



How does ransomware work?



What are common cybersecurity threats?



📈 Portfolio Value

Shows full-stack development with FastAPI and Streamlit.



Demonstrates local AI and RAG workflow skills.



Fits a cybersecurity portfolio because it works with study notes and lab writeups.



Can be extended with PDFs, Docker, or more models later.



🔮 Future Improvements

Add PDF and DOCX support.



Add chat history.



Add Docker setup.



Add better source formatting.



Add model selection in the UI.

