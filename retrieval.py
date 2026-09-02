from __future__ import annotations

import os
import sys
import time

from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

load_dotenv()

# Read API key from Streamlit secrets when deployed on Streamlit Cloud
try:
    import streamlit as st
    if hasattr(st, "secrets") and "MISTRAL_API_KEY" in st.secrets:
        os.environ["MISTRAL_API_KEY"] = st.secrets["MISTRAL_API_KEY"]
except Exception:
    pass

CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_db")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
MISTRAL_MODEL = "mistral-small-latest"
TEMPERATURE = 0.0
MAX_RETRIES = 3
BASE_DELAY = 6

SYSTEM_PROMPT = """You are a factual assistant for HDFC Mutual Fund schemes. You have information only on these three schemes: HDFC Large Cap Fund, HDFC Flexi Cap Fund, and HDFC ELSS Tax Saver Fund.

Answer only using the retrieved context provided below, sourced exclusively from official HDFC AMC, SEBI, and AMFI documents.

RULES:
1. Answer only factual scheme questions: expense ratio, exit load, minimum SIP amount, lock-in period (ELSS only), riskometer, benchmark index, and how to download capital gains or tax statements.
2. Keep every answer to 3 sentences or fewer.
3. Always include exactly one source link from the retrieved context:
   Source: <url>
4. End every answer with: Last updated from sources: <date of the source document used>
5. If a question asks for opinion, recommendation, or advice (e.g. "should I invest", "is this a good fund", "which is better for me"), respond only with:
   "I can only share factual scheme details, not investment advice. For investor education, see https://www.amfiindia.com/investor"
6. If a question asks to compare fund performance or returns, respond only with:
   "I don't compare fund performance. For official returns data, refer to the factsheet: <relevant factsheet link>"
7. If a question contains personal information (PAN, Aadhaar, account number, OTP, email, phone number), respond only with:
   "I can't process personal or account details. Please contact HDFC AMC directly at 1800 3010 6767."
   Do not repeat or echo the personal information back in your response.
8. If a question is about a mutual fund scheme outside these three, respond only with:
   "I only have information on HDFC Large Cap Fund, HDFC Flexi Cap Fund, and HDFC ELSS Tax Saver Fund."
9. If the retrieved context does not contain the answer, respond only with:
   "I don't have that information in my current sources. Please visit https://www.hdfcfund.com for complete scheme details."
10. Never guess, infer, or use information outside the retrieved context below.

DISCLAIMER shown to users:
"Facts-only. No investment advice. Sources: HDFC AMC, SEBI, AMFI official pages only."

Context: {retrieved_chunks}
Question: {user_question}"""


def detect_scheme(question: str) -> str | None:
    q_lower = question.lower()
    if "large cap" in q_lower:
        return "Large Cap"
    if "flexi cap" in q_lower:
        return "Flexi Cap"
    if any(kw in q_lower for kw in ["elss", "tax saver", "tax saving", "80c"]):
        return "ELSS"
    return None


def retrieve_chunks(question: str, top_k: int = 6, chroma_path: str = CHROMA_PATH) -> list[Document]:
    scheme = detect_scheme(question)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vectorstore = Chroma(
        persist_directory=chroma_path,
        embedding_function=embeddings,
    )

    filter_dict: dict[str, str] | None = None
    if scheme:
        filter_dict = {"scheme_name": scheme}

    chunks = vectorstore.similarity_search(
        question,
        k=top_k,
        filter=filter_dict,
    )
    return chunks


def format_prompt(question: str, chunks: list[Document]) -> str:
    formatted_chunks = []
    for i, doc in enumerate(chunks, 1):
        source_url = doc.metadata.get("source_url", "N/A")
        scheme_name = doc.metadata.get("scheme_name", "General")
        doc_type = doc.metadata.get("doc_type", "General")
        formatted_chunks.append(
            f"--- Chunk {i} ---\n"
            f"Source URL: {source_url}\n"
            f"Scheme: {scheme_name}\n"
            f"Doc Type: {doc_type}\n"
            f"Content:\n{doc.page_content}"
        )

    retrieved_chunks_str = "\n\n".join(formatted_chunks)
    return SYSTEM_PROMPT.format(
        retrieved_chunks=retrieved_chunks_str,
        user_question=question,
    )


def _call_mistral(prompt_text: str, retries: int = MAX_RETRIES) -> str | None:
    from mistralai import Mistral

    client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))
    messages = [{"role": "user", "content": prompt_text}]

    for attempt in range(1, retries + 1):
        try:
            response = client.chat.complete(
                model=MISTRAL_MODEL,
                messages=messages,
                temperature=TEMPERATURE,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            err_str = str(e)
            if "rate" in err_str.lower() or "429" in err_str or "context" in err_str.lower():
                if attempt < retries:
                    delay = BASE_DELAY * attempt
                    time.sleep(delay)
                    continue
                else:
                    print(f"Mistral API failed after {retries} retries. Error: {err_str}", file=sys.stderr)
                    return None
            else:
                print(f"Unexpected Mistral error: {e}", file=sys.stderr)
                return None

    return None


def retrieve_and_answer(question: str, top_k: int = 6) -> str | None:
    """Full pipeline: retrieve chunks → format prompt → call Mistral → return answer."""
    # Expand query to improve retrieval for common question types
    lower_q = question.lower()
    expanded_question = question

    if "expense ratio" in lower_q or "ter" in lower_q or "expense" in lower_q:
        expanded_question = question + " TER total expense ratio recurring expenses percentage NAV"
    elif "exit load" in lower_q:
        expanded_question = question + " exit load redemption charges load structure"
    elif "minimum sip" in lower_q or "minimum investment" in lower_q:
        expanded_question = question + " minimum SIP amount application investment"
    elif "benchmark" in lower_q:
        expanded_question = question + " benchmark index NSE BSE NIFTY"
    elif "lock-in" in lower_q or "lock in" in lower_q:
        expanded_question = question + " lock-in period years ELSS tax saver mandatory holding"
    elif "riskometer" in lower_q or "risk" in lower_q:
        expanded_question = question + " riskometer risk level very high moderately high"
    elif "statement" in lower_q or "capital gains" in lower_q:
        expanded_question = question + " capital gains statement download tax document CAMS KFintech"

    chunks = retrieve_chunks(expanded_question, top_k=top_k)
    if not chunks:
        chunks = retrieve_chunks(question, top_k=top_k, chroma_path=CHROMA_PATH)
        if not chunks:
            return (
                "I don't have that information in my current sources. "
                "Please visit https://www.hdfcfund.com for complete scheme details."
            )

    prompt = format_prompt(question, chunks)
    answer = _call_mistral(prompt)
    return answer


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_q = " ".join(sys.argv[1:])
    else:
        user_q = "What is the expense ratio of HDFC Large Cap Fund?"

    print(f"Question: {user_q}\n")
    print("Retrieving and generating answer via Mistral AI...")
    ans = retrieve_and_answer(user_q)
    print(f"\nAnswer:\n{ans}")