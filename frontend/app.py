import streamlit as st
import requests
import os

# Configure page
st.set_page_config(
    page_title="HR Policy Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Get backend URL from environment variable or use local
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Sidebar for document upload
with st.sidebar:
    st.header("📂 HR Document Upload")
    st.markdown("Upload your HR policy documents (PDF or Word)")
    
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if st.button("Process Documents", type="primary"):
        if uploaded_files:
            with st.spinner("Processing documents..."):
                files = [("files", file) for file in uploaded_files]
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/upload",
                        files=files
                    )
                    if response.status_code == 200:
                        st.success("Documents processed successfully!")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {str(e)}")
        else:
            st.warning("Please upload files first")

# Main chat interface
st.title("🤖 HR Policy Chatbot")
st.caption("Ask questions about your company's HR policies")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about HR policies..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/ask",
                    json={"text": prompt}
                )
                
                if response.status_code == 200:
                    answer = response.json().get("answer", "No answer found")
                else:
                    answer = f"Error: {response.json().get('detail', 'Unknown error')}"
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
