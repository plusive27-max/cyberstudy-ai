from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List
import os

# FIXED IMPORTS for modern LangChain + Python 3.14
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

app = FastAPI(title="CyberStudy AI Backend")

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []

# Paths
DATA_PATH = "backend/data/docs"
DB_PATH = "backend/data/chroma"

# Global RAG pipeline (lazy init)
rag_chain = None
vectorstore = None

def get_rag_pipeline():
    global rag_chain, vectorstore
    if vectorstore is None:
        # Load and split documents
        os.makedirs(DATA_PATH, exist_ok=True)
        loader = DirectoryLoader(DATA_PATH, glob="**/*.txt", loader_cls=TextLoader)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        
        # Embeddings and vector store
        embeddings = OllamaEmbeddings(model="mxbai-embed-large")
        vectorstore = Chroma.from_documents(
            documents=splits, 
            embedding=embeddings, 
            persist_directory=DB_PATH
        )
        
        # LLM
        llm = ChatOllama(model="llama3.2")
        
        # RAG prompt
        template = """Answer the question based only on the following context:
{context}

Question: {question}

Answer:"""
        prompt = ChatPromptTemplate.from_template(template)
        
        # FIXED RAG chain using retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        
        def format_docs(docs):
            return "\\n\\n".join(doc.page_content for doc in docs)
        
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt 
            | llm 
            | StrOutputParser()
        )
    return rag_chain

@app.get("/")
def read_root():
    return {"message": "CyberStudy AI Backend with RAG is running"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        chain = get_rag_pipeline()
        answer = chain.invoke(request.question)
        
        # FIXED sources retrieval
        embeddings = OllamaEmbeddings(model="mxbai-embed-large")
        db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
        retriever = db.as_retriever(search_kwargs={"k": 2})
        sources = retriever.invoke(request.question)
        source_names = [doc.metadata.get("source", "unknown") for doc in sources]
        
        return ChatResponse(answer=answer, sources=source_names)
    except Exception as e:
        return ChatResponse(answer=f"Error: {str(e)}", sources=[])

@app.post("/add-docs/")
async def add_docs(file: UploadFile = File(...)):
    os.makedirs(DATA_PATH, exist_ok=True)
    file_path = os.path.join(DATA_PATH, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"message": f"Added {file.filename}"}
