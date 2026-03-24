from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import logging

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="CyberStudy AI Backend", version="2.0.0")

# ── Config ───────────────────────────────────────────────────────────────────
DATA_PATH = os.getenv("DATA_PATH", "backend/data/docs")
DB_PATH   = os.getenv("DB_PATH",   "backend/data/chroma")
EMBED_MODEL = os.getenv("EMBED_MODEL", "mxbai-embed-large")
LLM_MODEL   = os.getenv("LLM_MODEL",  "llama3.2")

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}

RAG_PROMPT_TEMPLATE = """You are a cybersecurity study assistant.
Answer the question using ONLY the context below.
If you don't know, say so — don't make anything up.

Context:
{context}

Question: {question}

Answer:"""

# ── Schemas ──────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[dict]] = []   # [{"role": "user"|"assistant", "content": "..."}]

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []

# ── RAG state (module-level singletons) ──────────────────────────────────────
_embeddings: Optional[OllamaEmbeddings] = None
_vectorstore: Optional[Chroma] = None
_rag_chain = None


def _get_embeddings() -> OllamaEmbeddings:
    """Return a shared embeddings instance (created once)."""
    global _embeddings
    if _embeddings is None:
        logger.info("Initialising embeddings model: %s", EMBED_MODEL)
        _embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    return _embeddings


def _load_documents():
    """Load .txt, .pdf, and .docx files from DATA_PATH."""
    os.makedirs(DATA_PATH, exist_ok=True)
    all_docs = []

    loaders = {
        "**/*.txt":  lambda p: TextLoader(p, encoding="utf-8"),
        "**/*.pdf":  PyPDFLoader,
        "**/*.docx": Docx2txtLoader,
    }

    for glob_pattern, loader_cls in loaders.items():
        loader = DirectoryLoader(DATA_PATH, glob=glob_pattern, loader_cls=loader_cls, silent_errors=True)
        try:
            docs = loader.load()
            all_docs.extend(docs)
            logger.info("Loaded %d docs matching %s", len(docs), glob_pattern)
        except Exception as exc:
            logger.warning("Could not load %s: %s", glob_pattern, exc)

    return all_docs


def _build_vectorstore() -> Chroma:
    """Index all documents and return a Chroma vectorstore."""
    docs = _load_documents()
    if not docs:
        raise RuntimeError(
            f"No documents found in '{DATA_PATH}'. "
            "Upload a .txt / .pdf / .docx file first via POST /add-docs."
        )

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    logger.info("Split into %d chunks", len(splits))

    vs = Chroma.from_documents(
        documents=splits,
        embedding=_get_embeddings(),
        persist_directory=DB_PATH,
    )
    logger.info("Vectorstore built and persisted to %s", DB_PATH)
    return vs


def _get_vectorstore() -> Chroma:
    """Return the shared vectorstore, building it if needed."""
    global _vectorstore
    if _vectorstore is None:
        # Try loading an existing persisted store first
        if os.path.exists(DB_PATH) and os.listdir(DB_PATH):
            logger.info("Loading existing vectorstore from %s", DB_PATH)
            _vectorstore = Chroma(
                persist_directory=DB_PATH,
                embedding_function=_get_embeddings(),
            )
        else:
            _vectorstore = _build_vectorstore()
    return _vectorstore


def _get_rag_chain():
    """Return the shared RAG chain, building it if needed."""
    global _rag_chain
    if _rag_chain is None:
        retriever = _get_vectorstore().as_retriever(search_kwargs={"k": 4})
        prompt    = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        llm       = ChatOllama(model=LLM_MODEL)

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
    """Clear all cached singletons so the next request rebuilds from scratch."""
    global _embeddings, _vectorstore, _rag_chain
    _embeddings  = None
    _vectorstore = None
    _rag_chain   = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "message": "CyberStudy AI backend is running"}


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """Answer a cybersecurity question using RAG over your uploaded documents."""
    try:
        chain = _get_rag_chain()
        answer = chain.invoke(request.question)

        # Reuse the already-initialised vectorstore — no second Chroma instance
        sources_docs = _get_vectorstore().as_retriever(
            search_kwargs={"k": 2}
        ).invoke(request.question)
        sources = list({doc.metadata.get("source", "unknown") for doc in sources_docs})

        return ChatResponse(answer=answer, sources=sources)

    except RuntimeError as exc:
        # Friendly error when there are no docs yet
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during /chat")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")


@app.post("/add-docs", tags=["Documents"])
async def add_docs(file: UploadFile = File(...)):
    """Upload a .txt, .pdf, or .docx document and re-index the knowledge base."""
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Allowed: {SUPPORTED_EXTENSIONS}",
        )

    os.makedirs(DATA_PATH, exist_ok=True)
    dest = os.path.join(DATA_PATH, file.filename)

    with open(dest, "wb") as f:
        f.write(await file.read())

    logger.info("Uploaded: %s — resetting RAG pipeline", file.filename)
    _reset_pipeline()   # force re-index on next /chat call

    return {"message": f"'{file.filename}' uploaded and knowledge base will re-index on next query."}


@app.delete("/reset", tags=["Documents"])
def reset_index():
    """Wipe the vectorstore and force a full re-index on the next /chat call."""
    import shutil
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
        logger.info("Vectorstore deleted from %s", DB_PATH)
    _reset_pipeline()
    return {"message": "Knowledge base cleared. Upload documents and call /chat to re-index."}


@app.get("/docs-list", tags=["Documents"])
def list_docs():
    """List all documents currently in the knowledge base folder."""
    if not os.path.exists(DATA_PATH):
        return {"documents": []}
    files = [
        f for f in os.listdir(DATA_PATH)
        if os.path.splitext(f)[-1].lower() in SUPPORTED_EXTENSIONS
    ]
    return {"documents": files, "count": len(files)}
