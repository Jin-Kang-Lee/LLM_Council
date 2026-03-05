"""
Retriever utilities for the LLM Council reference library.
"""

from __future__ import annotations

import os

import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from config import VECTOR_DB_PATH

COLLECTION_NAME = "council_reference"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _infer_filter(query: str) -> dict | None:
    q = query.lower()
    candidates: list[tuple[str, str]] = []

    if "asc 606" in q or "asc606" in q:
        candidates.append(("standard", "ASC606"))
    if "asc 842" in q or "asc842" in q:
        candidates.append(("standard", "ASC842"))
    if "asc 326" in q or "asc326" in q or "cecl" in q:
        candidates.append(("standard", "ASC326"))

    if "sector margin" in q or "sector margins" in q:
        candidates.append(("topic", "sector_margins"))
    if "credit rating" in q or "default spread" in q or "interest coverage" in q:
        candidates.append(("topic", "credit_rating"))
    if "debt sector" in q or "debt fundamentals" in q:
        candidates.append(("topic", "debt_sector_fundamentals"))
    if "federal reserve" in q or " macro" in q or "fed " in q:
        candidates.append(("doc_type", "macro"))

    if len(candidates) == 1:
        key, value = candidates[0]
        return {key: value}

    return None


def _apply_filter(results: list, filter_dict: dict | None, k: int) -> list:
    if not filter_dict:
        return results[:k]

    key, value = next(iter(filter_dict.items()))
    matches = [doc for doc in results if doc.metadata.get(key) == value]
    if len(matches) >= k:
        return matches[:k]

    remainder = [doc for doc in results if doc.metadata.get(key) != value]
    return (matches + remainder)[:k]


def get_council_context(query: str, k: int = 4) -> str:
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    store = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )

    fetch_k = max(k * 3, 12)
    results = store.similarity_search(query, k=fetch_k)
    if not results:
        return ""

    filter_dict = _infer_filter(query)
    results = _apply_filter(results, filter_dict, k)

    chunks = []
    for doc in results:
        source = doc.metadata.get("source", "unknown")
        filename = os.path.basename(source)
        chunks.append(f"[{filename}]\n{doc.page_content}".strip())

    return "\n\n---\n\n".join(chunks)
