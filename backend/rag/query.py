"""
CLI helper to query the RAG reference library.

Usage:
  python backend/rag/query.py "your query" --k 3 --max_chars 800
"""

from __future__ import annotations

import argparse
import os
import sys


def _ensure_backend_on_path() -> None:
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the reference library RAG store")
    parser.add_argument("query", type=str, help="Query text")
    parser.add_argument("--k", type=int, default=4, help="Number of chunks to return")
    parser.add_argument(
        "--max_chars",
        type=int,
        default=1200,
        help="Max characters per chunk (0 for no trimming)",
    )
    args = parser.parse_args()

    _ensure_backend_on_path()
    from rag.retriever import get_council_context

    text = get_council_context(args.query, k=args.k)
    if not text:
        print("No results.")
        return

    chunks = text.split("\n\n---\n\n")
    for idx, chunk in enumerate(chunks, start=1):
        output = chunk
        if args.max_chars and len(output) > args.max_chars:
            output = output[: args.max_chars].rstrip() + "..."
        print(output)
        if idx < len(chunks):
            print("\n---\n")


if __name__ == "__main__":
    main()
