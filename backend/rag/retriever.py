"""
Retriever utilities for the LLM Council reference library.
"""

from __future__ import annotations

import os
from typing import Iterable, List, Tuple

import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from config import (
    VECTOR_DB_PATH,
    RAG_FETCH_K,
    RAG_MAX_CHUNKS,
    RAG_MAX_CHUNK_CHARS,
    RAG_MAX_CONTEXT_CHARS,
    RAG_MAX_DISTANCE,
    RAG_MAX_QUERY_CHARS,
    RAG_MIN_QUERY_CHARS,
    RAG_EMBEDDING_MODEL,
)
from rag.guardrails import is_low_quality_chunk, is_suspicious_chunk, normalize_whitespace, sanitize_query
from rag.reranker import rerank

COLLECTION_NAME = "council_reference"
EMBEDDING_MODEL = RAG_EMBEDDING_MODEL

# Module-level flag — checked once per process, not on every query
_db_ready: bool = False


def ensure_ingested() -> None:
    """
    Check whether the vector DB has been populated. If the collection is
    missing or empty, run ingest() automatically.

    Safe to call multiple times — skips the check after the first success.
    """
    global _db_ready
    if _db_ready:
        return

    try:
        client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        collection = client.get_or_create_collection(COLLECTION_NAME)
        count = collection.count()
        if count == 0:
            print("[RAG] Vector DB is empty — running auto-ingest...")
            from rag.ingest import ingest
            ingest(reset=False)
            print("[RAG] Auto-ingest complete.")
        else:
            print(f"[RAG] Vector DB ready ({count} chunks).")
        _db_ready = True
    except Exception as e:
        print(f"[RAG] Auto-ingest failed: {e}. Retrieval may return empty context.")


def build_shared_reference_query(content: str) -> str:
    if not content:
        return ""

    condensed = " ".join(content.split())
    if not condensed:
        return ""

    snippet = condensed[:1200]
    if len(condensed) > 1600:
        snippet = f"{snippet} ... {condensed[-200:]}"

    return f"Shared reference lookup for earnings analysis. Context: {snippet}"


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


def _apply_filter(
    results: List[Tuple[object, float]],
    filter_dict: dict | None,
    k: int,
    max_distance: float | None,
) -> List[Tuple[object, float]]:
    filtered: List[Tuple[object, float]] = []
    for doc, score in results:
        if max_distance is not None and score > max_distance:
            continue
        filtered.append((doc, score))

    if not filter_dict:
        return filtered[:k]

    key, value = next(iter(filter_dict.items()))
    matches = [(doc, score) for doc, score in filtered if doc.metadata.get(key) == value]
    if len(matches) >= k:
        return matches[:k]

    remainder = [(doc, score) for doc, score in filtered if doc.metadata.get(key) != value]
    return (matches + remainder)[:k]


def _format_source(doc: object) -> str:
    metadata = getattr(doc, "metadata", {}) or {}
    source = metadata.get("source_name") or metadata.get("source") or "unknown"
    filename = os.path.basename(source)
    header_1 = metadata.get("Header 1")
    header_2 = metadata.get("Header 2")
    if header_1 and header_2:
        return f"{filename} | {header_1} > {header_2}"
    if header_1:
        return f"{filename} | {header_1}"
    return filename


def _trim_chunk(text: str, max_chars: int) -> str:
    if not max_chars or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def _iter_chunks(results: Iterable[Tuple[object, float]]) -> list[str]:
    chunks: list[str] = []
    total_chars = 0
    chunk_index = 1
    seen_contents: set[str] = set()
    for doc, _score in results:
        content = getattr(doc, "page_content", "") or ""
        content = content.strip()
        if not content or is_suspicious_chunk(content) or is_low_quality_chunk(content):
            continue

        content = _trim_chunk(content, RAG_MAX_CHUNK_CHARS)
        normalized = normalize_whitespace(content).lower()
        if normalized in seen_contents:
            continue
        seen_contents.add(normalized)

        label = _format_source(doc)
        block = f"[C{chunk_index}] {label}\n{content}".strip()

        if total_chars + len(block) > RAG_MAX_CONTEXT_CHARS:
            break

        chunks.append(block)
        total_chars += len(block)
        chunk_index += 1

    return chunks


def get_council_context(query: str, k: int = 4) -> str:
    ensure_ingested()

    cleaned_query = sanitize_query(query, RAG_MAX_QUERY_CHARS, RAG_MIN_QUERY_CHARS)
    if not cleaned_query:
        return ""

    k = max(1, min(k, RAG_MAX_CHUNKS))

    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    store = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )

    fetch_k = max(k * 3, RAG_FETCH_K)
    try:
        results = store.similarity_search_with_score(cleaned_query, k=fetch_k)
    except AttributeError:
        docs = store.similarity_search(cleaned_query, k=fetch_k)
        results = [(doc, 0.0) for doc in docs]

    if not results:
        return ""

    results = rerank(cleaned_query, results)
    filter_dict = _infer_filter(cleaned_query)
    results = _apply_filter(results, filter_dict, k, RAG_MAX_DISTANCE)

    chunks = _iter_chunks(results)
    return "\n\n---\n\n".join(chunks)
