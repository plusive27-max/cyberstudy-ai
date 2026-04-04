from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
import uuid
from werkzeug.utils import secure_filename

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ── Config ───────────────────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY", "CHANGE_ME_IN_PRODUCTION_please_use_strong_key")
DATA_PATH = os.getenv("DATA_PATH", "/app/backend/data/docs")
DB_PATH = os.getenv("DB_PATH", "/app/backend/data/chroma")
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}

RAG_PROMPT_TEMPLATE = """You are a cybersecurity study assistant.
Answer the question using ONLY the context below.
If you don't know, say so — don't make anything up.

Context:
{context}

Question: {question}

Answer:"""

# ── Security ─────────────────────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)

def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials or credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return credentials.credentials

# ── Logging & App ────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CyberStudy AI Backend", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schemas ──────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[dict]] = []   # ignored for now

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []

# ── RAG state (singletons) ───────────────────────────────────────────────────
_embeddings: Optional[OllamaEmbeddings] = None
_vectorstore: Optional[Chroma] = None
_rag_chain = None

def _get_embeddings() -> OllamaEmbeddings:
    global _embeddings
    if _embeddings is None:
        logger.info("Initialising embeddings: %s", os.getenv("EMBED_MODEL", "mxbai-embed-large"))
        _embeddings = OllamaEmbeddings(model=os.getenv("EMBED_MODEL", "mxbai-embed-large"))
    return _embeddings

def _load_documents():
    os.makedirs(DATA_PATH, exist_ok=True)
    all_docs = []
    loaders = {
        "**/*.txt": lambda p: TextLoader(p, encoding="utf-8"),
        "**/*.pdf": PyPDFLoader,
        "**/*.docx": Docx2txtLoader,
    }
    for glob_pattern, loader_cls in loaders.items():
        loader = DirectoryLoader(DATA_PATH, glob=glob_pattern, loader_cls=loader_cls, silent_errors=True)
        try:
            docs = loader.load()
            all_docs.extend(docs)
            logger.info("Loaded %d docs for %s", len(docs), glob_pattern)
        except Exception as exc:
            logger.warning("Loader error %s: %s", glob_pattern, exc)
    return all_docs

def _build_vectorstore() -> Chroma:
    docs = _load_documents()
    if not docs:
        raise RuntimeError(f"No documents in '{DATA_PATH}'. Upload first via /add-docs.")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    logger.info("Split into %d chunks", len(splits))
    vs = Chroma.from_documents(
        documents=splits,
        embedding=_get_embeddings(),
        persist_directory=DB_PATH,
    )
    logger.info("Vectorstore built → %s", DB_PATH)
    return vs

def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        if os.path.exists(DB_PATH) and os.listdir(DB_PATH):
            logger.info("Loading existing vectorstore")
            _vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=_get_embeddings())
        else:
            _vectorstore = _build_vectorstore()
    return _vectorstore

def _get_rag_chain():
    global _rag_chain
    if _rag_chain is None:
        retriever = _get_vectorstore().as_retriever(search_kwargs={"k": 4})
        prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        llm = ChatOllama(model=os.getenv("LLM_MODEL", "llama3.2"))

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        _rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        logger.info("RAG chain ready")
    return _rag_chain

def _reset_pipeline():
    global _embeddings, _vectorstore, _rag_chain
    _embeddings = _vectorstore = _rag_chain = None

# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "message": "CyberStudy AI backend is running"}

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest, _: str = Depends(verify_api_key)):
    try:
        chain = _get_rag_chain()
        answer = chain.invoke(request.question)
        sources_docs = _get_vectorstore().as_retriever(search_kwargs={"k": 2}).invoke(request.question)
        sources = list({doc.metadata.get("source", "unknown") for doc in sources_docs})
        return ChatResponse(answer=answer, sources=sources)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail="Internal error")

@app.post("/add-docs", tags=["Documents"])
async def add_docs(file: UploadFile = File(...), _: str = Depends(verify_api_key)):
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(415, f"Unsupported type '{ext}'. Allowed: {SUPPORTED_EXTENSIONS}")

    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 15 MB)")

    safe_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    dest = os.path.join(DATA_PATH, unique_name)

    # Prevent path traversal
    if not os.path.abspath(dest).startswith(os.path.abspath(DATA_PATH)):
        raise HTTPException(400, "Invalid filename")

    os.makedirs(DATA_PATH, exist_ok=True)
    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    logger.info("Uploaded secure: %s", unique_name)
    _reset_pipeline()
    return {"message": f"'{file.filename}' uploaded and will re-index on next query."}

@app.delete("/reset", tags=["Documents"])
def reset_index(_: str = Depends(verify_api_key)):
    import shutil
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
        logger.info("Vectorstore deleted")
    _reset_pipeline()
    return {"message": "Knowledge base cleared."}

@app.get("/docs-list", tags=["Documents"])
def list_docs(_: str = Depends(verify_api_key)):
    if not os.path.exists(DATA_PATH):
        return {"documents": []}
    files = [
        f for f in os.listdir(DATA_PATH)
        if os.path.isfile(os.path.join(DATA_PATH, f))
    ]
    return {"documents": files}