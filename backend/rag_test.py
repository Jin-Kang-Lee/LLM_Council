import os
import sys

from rag.retriever import get_council_context
import chromadb

query = "Risk Analyst needs relevant benchmarks and accounting guidance. Focus: ASC 606 revenue recognition, Damodaran sector margins, Damodaran debt sector fundamentals."

try:
    print("Testing get_council_context...")
    result = get_council_context(query)
    print("Result length:", len(result))
    if not result:
        print("Result is totally empty!")
    else:
        print("Sample:", result[:200])
except Exception as e:
    print(f"FAILED: {e}")
