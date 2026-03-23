import streamlit as st
import requests
import json

st.title("🛡️ CyberStudy AI")

# Chat input
question = st.chat_input("Ask about cybersecurity notes...")

if question:
    with st.chat_message("user"):
        st.write(question)
    
    # Call FastAPI backend
    response = requests.post(
        "http://localhost:8000/chat",
        json={"question": question}
    )
    
    if response.status_code == 200:
        data = response.json()
        with st.chat_message("assistant"):
            st.write(data["answer"])
            if data["sources"]:
                st.write("**Sources:**", ", ".join(data["sources"]))
    else:
        st.error(f"Error: {response.status_code}")
