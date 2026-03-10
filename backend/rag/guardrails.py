"""
RAG guardrails for query normalization and context filtering.
"""

from __future__ import annotations

import re
from typing import Iterable

_WHITESPACE_RE = re.compile(r"\s+")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")

_INJECTION_PHRASES = (
    "ignore previous",
    "disregard earlier",
    "system prompt",
    "developer message",
    "you are chatgpt",
    "act as",
    "jailbreak",
    "tool call",
    "override instructions",
    "follow these instructions",
    "confidential prompt",
)


def normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def sanitize_query(query: str, max_chars: int, min_chars: int) -> str:
    if not query:
        return ""

    cleaned = _CONTROL_RE.sub(" ", query)
    cleaned = normalize_whitespace(cleaned)

    if max_chars and len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip()

    if min_chars and len(cleaned) < min_chars:
        return ""

    return cleaned


def is_suspicious_chunk(text: str) -> bool:
    if not text:
        return True

    lowered = text.lower()
    return any(phrase in lowered for phrase in _INJECTION_PHRASES)


def dedupe_chunks(chunks: Iterable[str]) -> list[str]:
    seen = set()
    unique: list[str] = []
    for chunk in chunks:
        normalized = normalize_whitespace(chunk).lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(chunk)
    return unique
