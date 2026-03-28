"""
Ingest reference library markdown/text files into a persistent Chroma vector store.
"""

from __future__ import annotations

import os
from typing import List

import chromadb
from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

import sys
import os

# Add root directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import REFERENCE_LIB_PATH, VECTOR_DB_PATH

COLLECTION_NAME = "council_reference"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _derive_metadata(source_path: str) -> dict:
    filename = os.path.basename(source_path) if source_path else "unknown"
    lower = filename.lower()

    meta = {
        "source_name": filename,
        "doc_type": "reference",
    }

    if "pwc_asc606" in lower:
        meta.update({"doc_type": "asc_guidance", "standard": "ASC606", "source_org": "PwC"})
    elif "ey_asc842" in lower:
        meta.update({"doc_type": "asc_guidance", "standard": "ASC842", "source_org": "EY"})
    elif "ey_asc326" in lower:
        meta.update({"doc_type": "asc_guidance", "standard": "ASC326", "source_org": "EY"})
    elif "damodaran_credit_rating" in lower:
        meta.update({"doc_type": "benchmark", "topic": "credit_rating", "source_org": "Damodaran"})
    elif "damodaran_debt_sector_fundamentals" in lower:
        meta.update({
            "doc_type": "benchmark",
            "topic": "debt_sector_fundamentals",
            "source_org": "Damodaran",
        })
    elif "damodraran_sector_margins" in lower or "damodaran_sector_margins" in lower:
        meta.update({"doc_type": "benchmark", "topic": "sector_margins", "source_org": "Damodaran"})
    elif "fedreserve_macro" in lower or "fed_reserve_macro" in lower:
        meta.update({"doc_type": "macro", "topic": "macro", "source_org": "Federal Reserve"})

    return meta


def load_documents() -> List[Document]:
    loaders = [
        DirectoryLoader(
            REFERENCE_LIB_PATH,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"autodetect_encoding": True},
        ),
        DirectoryLoader(
            REFERENCE_LIB_PATH,
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"autodetect_encoding": True},
        ),
    ]

    documents: List[Document] = []
    for loader in loaders:
        documents.extend(loader.load())

    for doc in documents:
        source = doc.metadata.get("source", "")
        doc.metadata.update(_derive_metadata(source))

    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n## ", "\n### ", "\n", " ", ""],
    )

    split_docs: List[Document] = []
    for doc in documents:
        chunks = splitter.split_text(doc.page_content)
        if not chunks:
            continue
        for chunk_text in chunks:
            # Create a new Document for each chunk, preserving metadata
            split_docs.append(Document(page_content=chunk_text, metadata=doc.metadata.copy()))

    return split_docs


def ingest(reset: bool = True) -> None:
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)

    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    if reset:
        try:
            client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass

    documents = load_documents()
    split_docs = split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    store = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )
    
    # Add documents in batches to avoid any overhead issues
    store.add_documents(split_docs)

    print(f"✅ Ingestion Complete!")
    print(f"   - Files loaded: {len(documents)}")
    print(f"   - Chunks created: {len(split_docs)}")
    
    # Verify final count in the collection
    final_count = client.get_collection(COLLECTION_NAME).count()
    print(f"   - Final collection count: {final_count}")
    print(f"   - Persisted to: {VECTOR_DB_PATH}")


if __name__ == "__main__":
    ingest()
