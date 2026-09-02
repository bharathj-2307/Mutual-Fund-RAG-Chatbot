from tempfile import NamedTemporaryFile

import requests
from langchain.text_splitter import TokenTextSplitter
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

SCHEME_CATEGORIES = ["Large Cap", "Flexi Cap", "ELSS", "General"]
DOC_TYPES = ["SID", "KIM", "Factsheet", "FAQ", "General"]

SCHEME_KEYWORDS = {
    "large cap": "Large Cap",
    "flexi cap": "Flexi Cap",
    "elss": "ELSS",
    "tax saver": "ELSS",
}

DOC_TYPE_KEYWORDS = {
    "SID": "SID",
    "KIM": "KIM",
    "factsheet": "Factsheet",
    "overview": "FAQ",
    "capital gain": "FAQ",
    "investor corner": "FAQ",
}


def _infer_doc_type(description: str) -> str:
    desc_lower = description.lower()
    for keyword, doc_type in DOC_TYPE_KEYWORDS.items():
        if keyword.lower() in desc_lower:
            return doc_type
    return "General"


def _infer_scheme_name(header: str) -> str:
    header_lower = header.lower()
    for keyword, scheme in SCHEME_KEYWORDS.items():
        if keyword in header_lower:
            return scheme
    return "General"


def load_sources_from_md(filepath: str) -> list[dict[str, str]]:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sources: list[dict[str, str]] = []
    current_scheme_header = ""

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            current_scheme_header = stripped[3:].strip()
            continue

        if stripped.startswith("|") and current_scheme_header:
            cells = [c.strip() for c in stripped.split("|")]
            cells = [c for c in cells if c]
            if not cells or cells[0] in ("#",):
                continue
            if cells[0].replace(".", "").replace("-", "").isdigit() or (
                len(cells) >= 3 and cells[0] and not cells[0].startswith("---")
            ):
                if len(cells) < 3:
                    continue
                doc_type_desc = cells[1] if len(cells) > 1 else ""
                url = cells[2] if len(cells) > 2 else ""
                if not url.startswith("http"):
                    continue
                scheme_name = _infer_scheme_name(current_scheme_header)
                doc_type = _infer_doc_type(doc_type_desc)
                sources.append(
                    {
                        "url": url,
                        "scheme_name": scheme_name,
                        "doc_type": doc_type,
                    }
                )

    return sources


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _is_pdf_url(url: str) -> bool:
    return url.lower().strip().endswith(".pdf")


def _fetch_text(url: str) -> str:
    try:
        if _is_pdf_url(url):
            response = requests.get(url, timeout=60, headers=HEADERS)
            response.raise_for_status()
            with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            loader = PyPDFLoader(tmp_path)
            pages = loader.load()
            return "\n".join(
                page.page_content for page in pages if page.page_content.strip()
            )
        web_loader: WebBaseLoader = WebBaseLoader(
            url, requests_kwargs={"headers": HEADERS}
        )
        docs = web_loader.load()
        return "\n".join(
            doc.page_content for doc in docs if doc.page_content.strip()
        )
    except Exception as e:  # noqa: BLE001
        print(f"  ! Error fetching {url}: {e}")
        return ""


def _split_text(text: str) -> list[str]:
    text_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=50)
    return text_splitter.split_text(text)


def _build_documents(
    chunks: list[str],
    source_url: str,
    scheme_name: str,
    doc_type: str,
) -> list[Document]:
    documents = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    "source_url": source_url,
                    "scheme_name": scheme_name,
                    "doc_type": doc_type,
                },
            )
        )
    return documents


def ingest(
    sources: list[dict[str, str]],
    persist_directory: str = "chroma_db",
    model_name: str = "all-MiniLM-L6-v2",
) -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )

    for source in sources:
        url = source["url"]
        scheme_name = source.get("scheme_name", "General")
        doc_type = source.get("doc_type", "General")

        if scheme_name not in SCHEME_CATEGORIES:
            raise ValueError(
                f"Invalid scheme_name '{scheme_name}'. "
                f"Must be one of {SCHEME_CATEGORIES}."
            )
        if doc_type not in DOC_TYPES:
            raise ValueError(
                f"Invalid doc_type '{doc_type}'. "
                f"Must be one of {DOC_TYPES}."
            )

        print(f"Fetching: {url} [{scheme_name} / {doc_type}]")
        text = _fetch_text(url)
        chunks = _split_text(text)
        documents = _build_documents(chunks, url, scheme_name, doc_type)

        if documents:
            vectorstore.add_documents(documents)
            print(f"  -> Added {len(documents)} chunks.")
        else:
            print("  -> No content extracted.")

    vectorstore.persist()
    count = len(vectorstore.get()["ids"])
    print(f"\nIngestion complete. {count} total chunks stored in '{persist_directory}'.")
    return vectorstore


if __name__ == "__main__":
    sources = load_sources_from_md("source_list_final_v2.md")
    print(f"Loaded {len(sources)} sources from source_list_final_v2.md.\n")
    ingest(sources)