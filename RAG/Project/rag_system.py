print("Importing libraries...")
#loading and chunking libraries
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

# vector storage
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

#LECL libraries
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# Conversational memory
from langchain_core.messages import HumanMessage, AIMessage
print("libraries successfully imported!")


load_dotenv()
api_key = os.getenv("paid_api")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

print("API key loaded")

#Loading and Chunking Documents
data_path = r"C:\Users\owner\Desktop\Files_Deep_Learning\RAG\Project\documents"
# Loading document
documents = []
for file in os.listdir(data_path):
    file_path = os.path.join(data_path, file)

    if file.endswith(".txt"):
        loader = TextLoader(file_path, encoding='utf-8')
        documents.extend(loader.load())

    elif file.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        documents.extend(loader.load())
print("Documents loaded.")

#Chunking
text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap = 50)
chunks = text_splitter.split_documents(documents)
print("document loaded and chunked!")


### Storing embeddings in a vector database
#Creating embeddings and storing
embedding = OpenAIEmbeddings(model= "text-embedding-3-small", openai_api_key=api_key)
vectorstore = Chroma.from_documents(documents=chunks,
                                    embedding=embedding, persist_directory = "./chroma_db")

vectorstore.persist()
print(f"Embeddings created and saved to chroma_db")


## RAG Chain with LCEL
# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0,openai_api_key=api_key)

# Retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

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


## Initialising and activating conversational memory
# RAG CHAIN
from operator import itemgetter
rag_chain = (
    {
        "context": itemgetter("question")
        | retriever
        | format_docs,

        "chat_history": itemgetter("chat_history"),
        "question": itemgetter("question")
    }
    | prompt
    | llm
    | StrOutputParser()
)

print("RAG Chain created!")


## Running the RAG assistant
chat_history = []
print("Esther Kudoro Personal Assistant \nType either 'exit' or 'quit' to stop the program.")

while True:
    question = input("You: ")
    if question.lower() in ["exit", "quit"]:
        break
    answer = rag_chain.invoke({
        "question": question,
        "chat_history": chat_history
    })

    print(f"\nUser: {question}")
    print(f"Assistant: {answer}\n")

    chat_history.extend([
        HumanMessage(content=question),
        AIMessage(content=answer)
    ])