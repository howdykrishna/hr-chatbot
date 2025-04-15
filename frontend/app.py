import streamlit as st
import requests

st.set_page_config(page_title="HR Chatbot", page_icon="🤖")
st.title("HR Policy Chatbot")

# Replace with your Vercel backend URL (after deployment)
BACKEND_URL = "https://your-vercel-app.vercel.app"  # ⚠️ Update after deployment!

# Initialize chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Sidebar for document upload
with st.sidebar:
    st.header("📂 Upload HR Policies")
    uploaded_files = st.file_uploader(
        "Upload PDF/DOCX files",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )
    if st.button("Process Documents"):
        if uploaded_files:
            files = [("files", file) for file in uploaded_files]
            response = requests.post(f"{BACKEND_URL}/upload", files=files)
            if response.status_code == 200:
                st.success("Documents processed!")
            else:
                st.error("Failed to process documents.")
        else:
            st.warning("Please upload files first.")

# Chat input
if prompt := st.chat_input("Ask about HR policies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # Send question to backend
    response = requests.post(
        f"{BACKEND_URL}/ask",
        json={"text": prompt}
    )
    
    if response.status_code == 200:
        answer = response.json()["answer"]
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.chat_message("assistant").write(answer)
    else:
        st.error("Failed to get response from AI.")
