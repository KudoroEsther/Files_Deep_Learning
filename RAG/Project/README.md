# LinkedIn Profile RAG Assistant 🤖
## Problem being solved
A complete Retrieval-Augmented Generation (RAG) system built with LangChain that answers questions about Esther Kudoro's LinkedIn profile using ChromaDB for vector storage and conversational memory.

This project implements a Retrieval-Augmented Generation (RAG) system using the LangChain orchestration framework.
The goal of the system is to act as a personal AI assistant that can accurately answer questions about Esther Kudoro by retrieving relevant information from my personal documents and uses ChromaDB for vector storage and conversational memory.

## Documents Used
The system uses two main documents sources; LinkedIn-based documents and GitHub-based documents. The LinkedIn-based documents such as about_me.txt and education.txt represent my professional and academic background making ideal for grounded question and answering. The GitHub-based documents consists of files like github_overview.txt, repo_all_tasks.txt which reflect my practical coding experience, and allows the RAG system to answwer questions about my coding experience, learning progression, and Practical ML and python skills.

## How to Run the System
1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Environment variable**
 **Install dependencies**
```bash
export OPEN_API_KEY = "your_api_key"
```

3. **Open and Run the Notebook**


## Example Interactions
User: Where did you stuy electrical engineering?

Assistant: You studied Electrical and Electronics Engineering at Afe Babalola University, graduating with first-class honors.
Source: education.txt


User:

What machine learning projects have you worked on?

Assistant:

You developed a machine learning model for fault prediction in electrical transmission lines, using voltage and current signals and deploying the model with FastAPI.
Source: projects.txt

## What I learned
* How RAG systems reduce hallucinations by grounding LLM responses

* How chunk size and overlap affect retrieval quality

* How to persist and reuse vector databases

* How LCEL enables clean, modular RAG pipelines

* How conversational memory improves user experience

* The importance of well-structured documents for retrieval accuracy

## Future Improvements
If I were to extend this project, I would:

* Add metadata-based filtering (education, projects, GitHub, etc.)

* Implement automatic source citation formatting

* Add a Streamlit or Gradio UI

* Evaluate retrieval quality using test queries

* Introduce document versioning and updates

