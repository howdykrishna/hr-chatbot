from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
import tempfile

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store the vectorstore
vectorstore = None

class Question(BaseModel):
    text: str

@app.get("/")
async def health_check():
    return {"status": "healthy", "message": "HR Chatbot API is running"}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    global vectorstore
    documents = []
    
    for file in files:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name
        
        try:
            if file.filename.endswith(".pdf"):
                loader = PyPDFLoader(temp_path)
            elif file.filename.endswith(".docx"):
                loader = Docx2txtLoader(temp_path)
            else:
                loader = UnstructuredFileLoader(temp_path)
                
            documents.extend(loader.load())
        finally:
            os.unlink(temp_path)
    
    if documents:
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = text_splitter.split_documents(documents)
        
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(texts, embeddings)
        
        return {"status": "success", "message": f"Processed {len(documents)} documents"}
    else:
        raise HTTPException(status_code=400, detail="No valid documents found")

@app.post("/ask")
async def ask_question(question: Question):
    global vectorstore
    if not vectorstore:
        raise HTTPException(status_code=400, detail="Please upload documents first")
    
    try:
        llm = HuggingFaceHub(
            repo_id="google/flan-t5-large",
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
            model_kwargs={"temperature": 0.5, "max_length": 512}
        )
        
        prompt_template = """Use the following context to answer the HR policy question.
        If you don't know the answer, say you don't know. Be professional and concise.

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
