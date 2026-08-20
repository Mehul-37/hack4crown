# 📚 PDF RAG — Document Question Answering System

A simple Retrieval-Augmented Generation (RAG) system that allows users to ask questions about a PDF document and receive answers based only on the relevant content retrieved from the document.

This project was built to understand and implement the complete RAG pipeline using LangChain.

## 🚀 How It Works

The system follows this pipeline:

PDF Document
↓
PyPDFLoader
↓
Text Chunking
↓
Local Sentence Transformer Embeddings
↓
Chroma Vector Database
↓
Similarity Retrieval
↓
Gemini LLM
↓
Context-Aware Answer

### Components

- **PyPDFLoader** — Loads and extracts text from the PDF.
- **RecursiveCharacterTextSplitter** — Splits the document into smaller chunks.
- **Sentence Transformers** — Generates embeddings locally using `all-MiniLM-L6-v2`.
- **Chroma** — Stores and retrieves document embeddings locally.
- **Gemini** — Generates the final answer using the retrieved context.
- **LangChain** — Connects the different components of the RAG pipeline.

## ✨ Features

- 📄 Works with large PDF documents
- 🔍 Semantic search over document content
- 🧠 Uses local embeddings to reduce API usage
- 💾 Local Chroma vector database
- 🤖 Gemini-powered answer generation
- 🔒 API keys stored locally using `.env`
- ⚡ Simple and lightweight RAG implementation

## 🛠️ Tech Stack

- Python
- LangChain
- ChromaDB
- Sentence Transformers
- Hugging Face
- Google Gemini API

## 📦 Installation

Clone the repository:

```bash
git clone <YOUR_REPOSITORY_URL>
cd pdf-rag
