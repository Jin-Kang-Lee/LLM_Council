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

_INJECTION_RE = re.compile("|".join(re.escape(p) for p in _INJECTION_PHRASES), re.IGNORECASE)

_LOW_ALPHA_RATIO = 0.3
_MIN_CHUNK_CHARS = 50


def normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def sanitize_query(query: str, max_chars: int, min_chars: int) -> str:
    if not query:
        return ""

    cleaned = _CONTROL_RE.sub(" ", query)
    cleaned = normalize_whitespace(cleaned)
    if cleaned:
        cleaned = _INJECTION_RE.sub(" ", cleaned)
        cleaned = normalize_whitespace(cleaned)

    if max_chars and len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip()

    if min_chars and len(cleaned) < min_chars:
        return ""

    if cleaned and _alpha_ratio(cleaned) < _LOW_ALPHA_RATIO:
        return ""

    return cleaned


def is_suspicious_chunk(text: str) -> bool:
    if not text:
        return True

    lowered = text.lower()
    return any(phrase in lowered for phrase in _INJECTION_PHRASES)


def _alpha_ratio(text: str) -> float:
    if not text:
        return 0.0
    alpha = sum(1 for ch in text if ch.isalpha())
    return alpha / max(1, len(text))


def is_low_quality_chunk(text: str) -> bool:
    if not text:
        return True
    if len(text.strip()) < _MIN_CHUNK_CHARS:
        return True
    if _alpha_ratio(text) < _LOW_ALPHA_RATIO:
        return True
    return False


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
