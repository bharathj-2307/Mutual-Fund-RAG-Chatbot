# Agent Guide - Mutual Fund RAG Chatbot

## Setup & Environment
- **Python Version**: Use 3.10+
- **Virtual Env**: `python -m venv venv && source venv/bin/activate`
- **Dependencies**: `pip install -r requirements.txt`
- **Env Vars**: Required in `.env`:
  - `OPENAI_API_KEY` (or chosen LLM provider)
  - `PINECONE_API_KEY` / `CHROMA_PATH` (if using external vector store)
  - `DATA_PATH`: Path to Mutual Fund documents (default: `./data`)

## Core Commands
- **Ingest Data**: `python src/ingest.py` (Parses PDFs and populates vector DB)
- **Run Chatbot**: `python src/main.py` or `streamlit run app.py`
- **Reset DB**: `rm -rf ./chroma_db` (if using local Chroma)

## RAG Pipeline Notes
- **Source Documents**: Place PDF prospectuses in `./data`.
- **Chunking Strategy**: Defaults to RecursiveCharacterTextSplitter (chunk: 1000, overlap: 200).
- **Retrieval**: Uses cosine similarity with top-k=5.
- **Prompt Template**: Defined in `src/prompts.py`. Modify here to change bot personality.

## Verification
- **Test Pipeline**: `pytest tests/test_rag.py`
- **Linting**: `ruff check .`
- **Type Checking**: `mypy src`
