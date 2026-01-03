from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

# Import your existing RAG components
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from operator import itemgetter
import os
from dotenv import load_dotenv

# Initialize FastAPI app
app = FastAPI(title="Esther Kudoro RAG Assistant API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()
api_key = os.getenv("paid_api")

# Initialize RAG components
embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embedding)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=api_key)

# System prompt
system_prompt_text = """
You are a personal RAG assistant answering questions strictly from the provided context about Esther Kudoro.

### INSTRUCTIONS:
1. Answer questions about professional experience, skills, repositories, and technical implementation details.
2. Use ONLY the context below. If the answer is not present, say "I do not have that information."
3. ALWAYS cite your sources implicitly by referring to the specific file or section.
4. Format all responses as clean plain text with no markdown or special characters.

### PRIVACY GUARDRAILS (CRITICAL):
You MUST REFUSE to answer questions about the following personal sensitive information, even if it might be present in the context:
- Age
- Date of birth
- Home Address
- Phone number
- Personal Email address
- Any other sensitive personal identifiers

If a user asks for this information, reply EXACTLY with:
"I cannot share personal or sensitive information such as contact details or age. Please ask about her professional experience or projects."

Context:
{context}

Question: {question}

Answer clearly and concisely.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt_text),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Build RAG chain
rag_chain = (
    {
        "context": itemgetter("question") | retriever | format_docs,
        "chat_history": itemgetter("chat_history"),
        "question": itemgetter("question")
    }
    | prompt
    | llm
    | StrOutputParser()
)

# Pydantic models
class Message(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List[Message]] = []

class QueryResponse(BaseModel):
    answer: str
    question: str

# Store sessions (in production, use Redis or a database)
sessions = {}

class SessionRequest(BaseModel):
    question: str
    session_id: str

# Endpoints
@app.get("/")
def read_root():
    return {"message": "Esther Kudoro RAG Assistant API", "status": "running"}

@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    """
    Query the RAG system with optional chat history.
    """
    try:
        # Convert Pydantic messages to LangChain messages
        chat_history = []
        for msg in request.chat_history:
            if msg.role == "user":
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                chat_history.append(AIMessage(content=msg.content))
        
        # Invoke RAG chain
        answer = rag_chain.invoke({
            "question": request.question,
            "chat_history": chat_history
        })
        
        return QueryResponse(answer=answer, question=request.question)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/{session_id}", response_model=QueryResponse)
def chat_with_session(session_id: str, request: QueryRequest):
    """
    Chat with session management. Chat history is stored per session_id.
    """
    try:
        # Initialize session if it doesn't exist
        if session_id not in sessions:
            sessions[session_id] = []
        
        # Get chat history from session
        chat_history = sessions[session_id]
        
        # Invoke RAG chain
        answer = rag_chain.invoke({
            "question": request.question,
            "chat_history": chat_history
        })
        
        # Update session history
        sessions[session_id].extend([
            HumanMessage(content=request.question),
            AIMessage(content=answer)
        ])
        
        return QueryResponse(answer=answer, question=request.question)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/{session_id}")
def clear_session(session_id: str):
    """
    Clear chat history for a specific session.
    """
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    return {"message": f"Session {session_id} not found"}

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "vectorstore": "loaded"}

# Run with: uvicorn filename:app --reload