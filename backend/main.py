from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate

app = FastAPI()

# Allow CORS (for frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store documents in memory (for demo; replace with DB in production)
vectorstore = None

class Question(BaseModel):
    text: str

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    global vectorstore
    documents = []
    
    for file in files:
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file.filename.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            loader = UnstructuredFileLoader(file_path)
            
        documents.extend(loader.load())
        os.remove(file_path)
    
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(texts, embeddings)
    
    return {"status": "success"}

@app.post("/ask")
async def ask_question(question: Question):
    global vectorstore
    if not vectorstore:
        raise HTTPException(status_code=400, detail="Please upload documents first")
    
    # Replace with your Hugging Face API key (free)
    llm = HuggingFaceHub(
        repo_id="google/flan-t5-large",
        huggingfacehub_api_token="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",  # 🔑 Replace this!
        model_kwargs={"temperature": 0.5, "max_length": 512}
    )
    
    prompt_template = """Answer the HR policy question based on the context. Be professional.
    If unsure, say "I don't know."

    Context: {context}
    Question: {question}
    Answer:"""
    
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    response = qa_chain.run(question.text)
    return {"answer": response}
