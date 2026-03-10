"""
Optional cross-encoder reranker for retrieval precision.
"""

from __future__ import annotations

from typing import List, Tuple, Iterable

from config import RAG_RERANK_ENABLED, RAG_RERANK_MODEL, RAG_RERANK_TOP_K

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import CrossEncoder
    except Exception:
        _model = False
        return _model
    _model = CrossEncoder(RAG_RERANK_MODEL)
    return _model


def rerank(
    query: str,
    results: List[Tuple[object, float]],
) -> List[Tuple[object, float]]:
    if not RAG_RERANK_ENABLED or not results:
        return results

    model = _load_model()
    if model is False:
        return results

    top_k = min(len(results), max(1, RAG_RERANK_TOP_K))
    rerank_slice = results[:top_k]
    rest = results[top_k:]

    pairs = [(query, getattr(doc, "page_content", "") or "") for doc, _score in rerank_slice]
    if not pairs:
        return results

    try:
        scores = model.predict(pairs)
    except Exception:
        return results

    reranked = sorted(
        ((doc, float(score)) for (doc, _), score in zip(rerank_slice, scores)),
        key=lambda item: item[1],
        reverse=True,
    )

    return reranked + rest
