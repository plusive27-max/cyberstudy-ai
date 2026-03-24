import streamlit as st
import requests
import os

# ── Config ───────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── Page setup ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CyberStudy AI",
    page_icon="🛡️",
    layout="centered",
)

# ── Session state defaults ───────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []          # [{role, content, sources}]

# ── Helpers ──────────────────────────────────────────────────────────────────
def post_question(question: str) -> dict:
    """Send a question to the backend and return the response dict."""
    resp = requests.post(
        f"{BACKEND_URL}/chat",
        json={"question": question},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def upload_file(file) -> str:
    """Upload a document to the backend. Returns a status message."""
    resp = requests.post(
        f"{BACKEND_URL}/add-docs",
        files={"file": (file.name, file.getvalue(), file.type)},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("message", "Uploaded successfully.")


def fetch_doc_list() -> list[str]:
    try:
        resp = requests.get(f"{BACKEND_URL}/docs-list", timeout=10)
        return resp.json().get("documents", [])
    except Exception:
        return []


def reset_index() -> str:
    resp = requests.delete(f"{BACKEND_URL}/reset", timeout=30)
    resp.raise_for_status()
    return resp.json().get("message", "Index cleared.")


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 Knowledge Base")

    uploaded = st.file_uploader(
        "Upload a document",
        type=["txt", "pdf", "docx"],
        help="Supported formats: .txt · .pdf · .docx",
    )
    if uploaded:
        with st.spinner(f"Uploading {uploaded.name}…"):
            try:
                msg = upload_file(uploaded)
                st.success(msg)
            except requests.HTTPError as e:
                detail = e.response.json().get("detail", str(e))
                st.error(f"Upload failed: {detail}")

    st.divider()
    st.subheader("📄 Indexed Documents")
    docs = fetch_doc_list()
    if docs:
        for d in docs:
            st.markdown(f"- `{d}`")
    else:
        st.caption("No documents indexed yet.")

    st.divider()
    if st.button("🗑️ Clear Knowledge Base", use_container_width=True):
        with st.spinner("Clearing…"):
            try:
                msg = reset_index()
                st.success(msg)
            except Exception as e:
                st.error(str(e))

    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Main chat area ────────────────────────────────────────────────────────────
st.title("🛡️ CyberStudy AI")
st.caption("Ask questions about your uploaded cybersecurity notes and writeups.")

# Render previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            with st.expander("📎 Sources"):
                for src in msg["sources"]:
                    st.markdown(f"- `{src}`")

# Chat input
question = st.chat_input("Ask about cybersecurity…")

if question:
    # Show and store the user message immediately
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    # Call backend and stream response
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                data = post_question(question)
                answer  = data.get("answer", "No answer returned.")
                sources = data.get("sources", [])

                st.write(answer)
                if sources:
                    with st.expander("📎 Sources"):
                        for src in sources:
                            st.markdown(f"- `{src}`")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })

            except requests.HTTPError as e:
                try:
                    detail = e.response.json().get("detail", str(e))
                except Exception:
                    detail = str(e)
                st.error(f"Backend error: {detail}")

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot reach the backend. "
                    "Make sure the FastAPI server is running on `localhost:8000`."
                )
