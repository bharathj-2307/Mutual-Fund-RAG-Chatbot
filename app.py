import re
import time

import streamlit as st

from retrieval import retrieve_and_answer

st.set_page_config(
    page_title="HDFC Mutual Fund FAQ Assistant",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- CUSTOM CSS ----------
st.markdown(
    """
    <style>
    html, body, .stApp {
        background-color: #FFFFFF !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    .stApp {
        border-top: 4px solid #00B386 !important;
    }
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 720px !important;
    }
    h1 {
        color: #1A1A1A !important;
        font-weight: 700 !important;
        font-size: 1.9rem !important;
        line-height: 1.3 !important;
        text-align: center !important;
        margin-bottom: 4px !important;
    }
    h3 {
        color: #1A1A1A !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        margin-top: 0 !important;
        margin-bottom: 12px !important;
    }
    h3 a, h2 a, h1 a {
        display: none !important;
    }
    .stButton > button {
        background-color: #00B386 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 11px !important;
        padding: 10px 6px !important;
        width: 100% !important;
        white-space: normal !important;
        line-height: 1.4 !important;
        height: auto !important;
        min-height: 80px !important;
        text-align: center !important;
        transition: background-color 0.15s ease !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    .stButton > button:hover,
    .stButton > button:focus,
    .stButton > button:active {
        background-color: #009E78 !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
        border: none !important;
    }
    .stTextInput input,
    .stTextInput input:focus,
    .stTextInput input:active {
        background-color: #FAFAFA !important;
        border-radius: 10px !important;
        font-size: 15px !important;
        padding: 12px 16px !important;
        color: #1A1A1A !important;
        border: 1.5px solid #E0E0E0 !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .stTextInput > div,
    .stTextInput > div > div,
    .stTextInput > div > div > div {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div {
        border: 1.5px solid #E0E0E0 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        background-color: #FAFAFA !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="input"]:focus-within > div {
        border-color: #00B386 !important;
        box-shadow: 0 0 0 2px rgba(0,179,134,0.15) !important;
    }
    button:focus { outline: none !important; box-shadow: none !important; }
    .stSpinner p { color: #00B386 !important; font-size: 14px !important; }
    div[data-testid="stAlertContainer"] { border-radius: 10px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- HEADER ----------
st.title("HDFC Mutual Fund FAQ Assistant")
st.markdown(
    '<p style="color:#666666; font-size:15px; text-align:center; margin-top:4px; margin-bottom:20px; line-height:1.5;">'
    "Get instant facts on HDFC Large Cap, Flexi Cap, and ELSS Tax Saver Fund — "
    "no advice, just verified data."
    "</p>",
    unsafe_allow_html=True,
)

# Disclaimer banner
st.markdown(
    '<div style="background:#E6FAF5; border-radius:10px; padding:12px 16px; margin-bottom:28px;">'
    '<span style="color:#00916E; font-size:13.5px; font-weight:500;">'
    "&#9432;&nbsp; Facts-only. No investment advice. "
    "Sources: HDFC AMC, SEBI, AMFI official pages only."
    "</span></div>",
    unsafe_allow_html=True,
)


# ---------- HELPERS ----------
def _has_personal_info(text: str) -> bool:
    patterns = [
        r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
        r"\b[0-9]{12}\b",
        r"\baccount\s*[0-9]+\b",
        r"\bOTP\b",
    ]
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def _safe_call(user_question: str, retries: int = 3, delay: int = 6):
    for attempt in range(1, retries + 1):
        try:
            return retrieve_and_answer(user_question)
        except Exception as err:
            err_str = str(err)
            if "429" in err_str or "rate" in err_str.lower() or "quota" in err_str.lower():
                if attempt < retries:
                    st.warning(f"Rate limit hit. Waiting {delay}s before retry (attempt {attempt}/{retries})...")
                    time.sleep(delay)
                    continue
                else:
                    st.error("Rate limit reached. Please wait a minute and try again, or check your Mistral API quota.")
                    return None
            else:
                st.error(f"An error occurred: {err}")
                return None
    return None


def _parse_answer(raw: str) -> dict:
    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
    answer_lines = []
    source_url = ""
    source_label = ""
    last_updated = ""

    for line in lines:
        if line.lower().startswith("source:"):
            url = line[7:].strip()
            source_url = url
            raw_name = url.rstrip("/").split("/")[-1]
            try:
                from urllib.parse import unquote
                raw_name = unquote(raw_name)
            except Exception:
                pass
            raw_name = raw_name.replace(".pdf", "").replace("%20", " ").replace("_", " ")
            source_label = raw_name[:80] + "..." if len(raw_name) > 80 else raw_name
        elif line.lower().startswith("last updated"):
            last_updated = line
        else:
            answer_lines.append(line)

    return {
        "answer_text": " ".join(answer_lines),
        "source_url": source_url,
        "source_label": source_label,
        "last_updated": last_updated,
    }


def _render_answer(raw: str):
    parsed = _parse_answer(raw)
    answer_text = parsed["answer_text"]
    source_url = parsed["source_url"]
    source_label = parsed["source_label"] or "View source document"
    last_updated = parsed["last_updated"]

    source_block = ""
    if source_url:
        source_block = (
            '<div style="margin-top:16px; padding-top:14px; border-top:1px solid #EFEFEF;">'
            '<span style="font-size:11px; font-weight:700; color:#AAAAAA; letter-spacing:0.8px; '
            'text-transform:uppercase;">Source</span><br>'
            f'<a href="{source_url}" target="_blank" style="color:#00916E; font-size:13.5px; '
            'font-weight:500; text-decoration:none; word-break:break-word;">'
            f'&#128196;&nbsp;{source_label}</a>'
            '</div>'
        )

    updated_block = ""
    if last_updated:
        updated_block = (
            '<div style="margin-top:10px;">'
            '<span style="font-size:11px; font-weight:700; color:#AAAAAA; letter-spacing:0.8px; '
            'text-transform:uppercase;">Last Updated</span><br>'
            f'<span style="font-size:13px; color:#888888;">{last_updated.replace("Last updated from sources:", "").strip()}</span>'
            '</div>'
        )

    st.markdown(
        '<div style="background:#FFFFFF; border:1.5px solid #E8E8E8; border-radius:14px; '
        'padding:24px 28px; margin-top:20px; box-shadow:0 2px 16px rgba(0,0,0,0.06);">'
        '<div style="display:flex; align-items:center; margin-bottom:14px;">'
        '<div style="width:8px; height:8px; background:#00B386; border-radius:50%; margin-right:10px;"></div>'
        '<span style="color:#00916E; font-size:11px; font-weight:700; letter-spacing:0.8px; text-transform:uppercase;">Answer</span>'
        '</div>'
        f'<div style="color:#1A1A1A; font-size:16px; line-height:1.8; font-weight:400;">{answer_text}</div>'
        + source_block
        + updated_block
        + '</div>',
        unsafe_allow_html=True,
    )


# ---------- ASK YOUR QUESTION ----------
st.subheader("Ask your question")

user_question = st.text_input(
    label="Your question",
    label_visibility="collapsed",
    placeholder="e.g., What is the exit load for HDFC Large Cap Fund?",
    key="text_input_field",
)

active_question = user_question.strip() or st.session_state.pop("active_question", "")

# ---------- ANSWER ----------
if active_question:
    if _has_personal_info(active_question):
        st.markdown(
            '<div style="background:#FFF3F3; border-left:4px solid #E05252; border-radius:10px; '
            'padding:16px 20px; margin-top:16px;">'
            '<p style="color:#C0392B; font-size:14px; font-weight:700; margin:0 0 6px 0;">⚠️ Privacy Notice</p>'
            '<p style="color:#444; font-size:15px; margin:0; line-height:1.6;">'
            "I can't process personal or account details. "
            "Please contact HDFC AMC directly at <strong>1800 3010 6767</strong>."
            "</p></div>",
            unsafe_allow_html=True,
        )
    else:
        with st.spinner("Fetching answer from official HDFC documents..."):
            answer = _safe_call(active_question)

        if answer:
            _render_answer(answer)
        else:
            st.markdown(
                '<div style="background:#FFFBF0; border-left:4px solid #F0A500; border-radius:10px; '
                'padding:16px 20px; margin-top:16px;">'
                '<p style="color:#7A5800; font-size:15px; margin:0; line-height:1.6;">'
                "No answer could be generated right now. Please try again in a few seconds."
                "</p></div>",
                unsafe_allow_html=True,
            )

# ---------- DIVIDER ----------
st.markdown(
    '<hr style="border:none; border-top:1px solid #F0F0F0; margin:36px 0 24px 0;">',
    unsafe_allow_html=True,
)

# ---------- SAMPLE QUESTIONS ----------
st.subheader("Try a sample question")

SAMPLE_QUESTIONS = [
    "What is the exit load for HDFC Large Cap Fund?",
    "What is the lock-in period for HDFC ELSS Tax Saver Fund?",
    "How do I download my capital gains statement?",
]

col1, col2, col3 = st.columns(3)
for col, q in zip([col1, col2, col3], SAMPLE_QUESTIONS):
    with col:
        if st.button(q, key=f"sample_{q[:20]}"):
            st.session_state["active_question"] = q
            st.rerun()

# ---------- FOOTER ----------
st.markdown(
    '<div style="margin-top:48px; padding-top:20px; border-top:1px solid #F4F4F4; text-align:center;">'
    '<p style="color:#CCCCCC; font-size:12px; margin:0; line-height:1.8;">'
    "Data sourced from HDFC AMC, SEBI, and AMFI official pages only.<br>"
    "Last ingestion: September 2026 &nbsp;·&nbsp; Not financial advice."
    "</p></div>",
    unsafe_allow_html=True,
)