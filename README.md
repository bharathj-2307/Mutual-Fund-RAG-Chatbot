# HDFC Mutual Fund FAQ Assistant

## Overview

A RAG-based FAQ chatbot that answers factual questions about HDFC Large Cap Fund, HDFC Flexi Cap Fund, and HDFC ELSS Tax Saver Fund using only official AMC, SEBI, and AMFI sources.

## Scope

- **AMC:** HDFC Mutual Fund
- **Schemes covered:**
  - HDFC Large Cap Fund
  - HDFC Flexi Cap Fund
  - HDFC ELSS Tax Saver Fund

## Setup

1. Clone the repo
   ```bash
   git clone <repo-url>
   cd <repo-dir>
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with:
   ```
   MISTRAL_API_KEY=your_key_here
   ```
4. Run ingestion:
   ```bash
   python ingest.py
   ```
5. Launch the app:
   ```bash
   streamlit run app.py
   ```

## Known Limits

- Only covers 3 HDFC schemes; questions about other funds will be declined
- HDFC ELSS Tax Saver SID is dated November 2024; Large Cap and Flexi Cap SIDs are dated November 2025
- No PII accepted or stored
- No investment advice or return comparisons provided
- Answers sourced from public documents only; may not reflect same-day NAV or fee changes

## Disclaimer

Facts-only. No investment advice. Sources: HDFC AMC, SEBI, AMFI official pages only.
