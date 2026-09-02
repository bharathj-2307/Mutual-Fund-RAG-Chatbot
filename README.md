# HDFC Mutual Fund FAQ Assistant

A RAG-based FAQ chatbot that answers factual questions about HDFC Mutual Fund schemes using only official AMC, SEBI, and AMFI sources. Built as part of a Product Management Fellowship milestone (W1 + W2 + W3).

🔗 **Live app:** https://hdfc-mutualfund-rag-chatbot.streamlit.app/

---

## Scope

**Product context:** Groww (mutual fund investment platform)

**AMC:** HDFC Mutual Fund

**Schemes covered:**
- HDFC Large Cap Fund (Direct Plan)
- HDFC Flexi Cap Fund (Direct Plan)
- HDFC ELSS Tax Saver Fund (Direct Plan)

**Sources:** 18 official URLs from hdfcfund.com, AMFI, and SEBI — factsheets, SID, KIM, TER disclosures, riskometer, and statement-download guides.

---

## What it does

- Answers factual scheme queries: expense ratio, exit load, lock-in period, riskometer, benchmark index, and how to download capital gains statements
- Shows one citation link per answer with a "Last updated" date
- Politely refuses opinion, advice, or portfolio questions with a redirect to AMFI investor education
- Blocks and does not echo personal information (PAN, Aadhaar, account numbers, OTPs)
- Redirects performance/returns questions to the official factsheet

---

## Setup steps

**1. Clone the repo**
```
git clone https://github.com/bharathj-2307/Mutual-Fund-RAG-Chatbot.git
cd Mutual-Fund-RAG-Chatbot
```

**2. Install dependencies**
```
pip install -r requirements.txt
```

**3. Add your API key**

Create a `.env` file in the project root:
```
MISTRAL_API_KEY=your_mistral_api_key_here
```

**4. Run ingestion (only needed if chroma_db is missing)**
```
python ingest.py
```

**5. Launch the app**
```
streamlit run app.py
```

---

## Tech stack

- **LLM:** Mistral AI (mistral-small-latest)
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **Vector store:** ChromaDB (local)
- **Framework:** LangChain
- **UI:** Streamlit
- **Hosting:** Streamlit Community Cloud

---

## Known limits

- Only covers 3 HDFC schemes — questions about other funds are declined
- Minimum SIP amount is not reliably retrieved from current source chunks (SID PDFs store this in tables that don't extract cleanly); users are redirected to hdfcfund.com
- Cross-scheme comparisons (e.g. "which fund has the lowest expense ratio") are not supported — each scheme is answered independently
- HDFC ELSS Tax Saver SID is dated November 2024; Large Cap and Flexi Cap SIDs are dated November 2025
- Answers sourced from public documents only — may not reflect same-day NAV or fee changes
- No PII accepted or stored at any point

---

## Disclaimer

Facts-only. No investment advice. Sources: HDFC AMC, SEBI, AMFI official pages only. This tool is for informational purposes only and does not constitute financial advice. Please consult a SEBI-registered investment advisor before making any investment decisions.
