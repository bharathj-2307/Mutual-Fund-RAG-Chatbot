# Agent Guide - Mutual Fund RAG Chatbot

## Setup & Environment
- **Python Version**: Use 3.9+
- **Virtual Env**: `python3 -m venv venv && source venv/bin/activate`
- **Dependencies**: `pip install -r requirements.txt`
- **Env Vars**: Optional `.env` for custom settings

## Core Commands
- **Ingest Data**: `python3 ingest.py` (Fetches URLs and populates vector DB)
- **Run Chatbot**: `python3 main.py` or `streamlit run app.py`
- **Reset DB**: `rm -rf ./chroma_db`

## RAG Pipeline Notes
- **Source Documents**: 18 URLs from hdfcfund.com, AMFI, SEBI (PDFs & web pages).
- **Chunking**: TokenTextSplitter — chunk_size=500, chunk_overlap=50.
- **Embeddings**: sentence-transformers `all-MiniLM-L6-v2` (local, no API key).
- **Vector Store**: ChromaDB (local, persisted in `chroma_db/`).
- **Metadata per chunk**: source_url, scheme_name (Large Cap / Flexi Cap / ELSS / General), doc_type (SID / KIM / Factsheet / FAQ / General).

## Verification
- **Test Pipeline**: `pytest tests/test_rag.py`
- **Linting**: `ruff check .`
- **Type Checking**: `mypy .`
