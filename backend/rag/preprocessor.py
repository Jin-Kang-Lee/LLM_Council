"""
Context Preprocessor — Map-Reduce pipeline for compacting earnings report content.

Splits the earnings report into chunks, queries the RAG library for each chunk,
merges them side-by-side into a compact summary, then stitches the summaries
together for the downstream agents.
"""

from __future__ import annotations

import asyncio
import re
from typing import Optional

import httpx

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from rag.retriever import get_council_context


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Approximate character size of each chunk fed to the merge step.
# ~1 500 chars ≈ 300–350 tokens, comfortable for a q2_K model.
CHUNK_SIZE = 1500

# Hard cap on the final merged context so we stay inside the model's window.
MAX_MERGED_CHARS = 8000

_MERGE_SYSTEM_PROMPT = """\
You are a financial data distillation engine.
You receive a CHUNK of an earnings report and the relevant ACCOUNTING REFERENCE
guidelines (from Damodaran / ASC standards) retrieved for that chunk.

Your job: produce a compact, dense summary that:
1. Retains every numerical figure, ratio, and named metric from the chunk.
2. Identifies which ASC standard or benchmark applies to each figure.
3. Flags any disclosure gaps explicitly (e.g., "CapEx not disclosed").
4. Strips all filler language ("We are pleased to report…", boilerplate, etc.).
5. Uses bullet points. Maximum 150 words.

Output ONLY the bullet-point summary. No preamble, no markdown fences.\
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """
    Split text into roughly equal chunks by paragraph boundaries.
    Falls back to hard-char splitting if paragraphs are too large.
    """
    paragraphs = re.split(r"\n{2,}", text.strip())
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current_len + len(para) > chunk_size and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)

    if current:
        chunks.append("\n\n".join(current))

    # Safety: hard-split any chunk that is still too large
    final: list[str] = []
    for chunk in chunks:
        if len(chunk) <= chunk_size * 1.5:
            final.append(chunk)
        else:
            for i in range(0, len(chunk), chunk_size):
                final.append(chunk[i : i + chunk_size])
    return final


async def _merge_single_chunk(
    chunk: str,
    rag_context: str,
    model: str,
    ollama_chat_url: str,
    semaphore: asyncio.Semaphore,
) -> str:
    """Call Ollama once to merge one chunk + its RAG context into a summary."""
    user_msg = (
        f"CHUNK:\n{chunk}\n\n"
        f"ACCOUNTING REFERENCE:\n{rag_context if rag_context else 'No reference retrieved.'}"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _MERGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "stream": False,
        "options": {"temperature": 0.1, "top_p": 0.9},
    }
    async with semaphore:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                resp = await client.post(ollama_chat_url, json=payload)
                resp.raise_for_status()
                data = resp.json()
            return data.get("message", {}).get("content", "").strip()
        except Exception as e:
            print(f"[Preprocessor] Merge failed for chunk: {e}")
            # Fall back to the raw chunk so agents still have some context
            return chunk[:600]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def preprocess_context(
    report_content: str,
    max_concurrent: int = 2,
) -> str:
    """
    Map-Reduce context preprocessor.

    Args:
        report_content: Full earnings report text (already formatted by format_for_agents).
        max_concurrent: Maximum parallel Ollama calls for the map step.

    Returns:
        A compact, merged context string ready to be sent to the analyst agents.
    """
    ollama_chat_url = f"{OLLAMA_BASE_URL}/api/chat"

    # ── Map phase ────────────────────────────────────────────────────────────
    chunks = _split_into_chunks(report_content)
    print(f"[Preprocessor] Split report into {len(chunks)} chunk(s).")

    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_chunk(idx: int, chunk: str) -> str:
        rag_ctx = get_council_context(chunk[:1200])
        print(f"[Preprocessor] Chunk {idx+1}/{len(chunks)} — RAG: {len(rag_ctx)} chars")
        summary = await _merge_single_chunk(
            chunk, rag_ctx, OLLAMA_MODEL, ollama_chat_url, semaphore
        )
        return summary

    summaries = await asyncio.gather(
        *[process_chunk(i, c) for i, c in enumerate(chunks)]
    )

    # ── Reduce phase ─────────────────────────────────────────────────────────
    merged = "\n\n---\n\n".join(s for s in summaries if s)

    # Trim to hard cap so we don't blow the agent's context window
    if len(merged) > MAX_MERGED_CHARS:
        merged = merged[:MAX_MERGED_CHARS] + "\n\n[...truncated for context window]"

    print(f"[Preprocessor] Merged context: {len(merged)} chars (from {len(report_content)} original).")
    return merged
