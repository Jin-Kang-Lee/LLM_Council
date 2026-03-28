
import sys
import os
sys.path.append(os.getcwd())

from rag.retriever import get_council_context

queries = [
    "Risk Analyst needs relevant benchmarks and accounting guidance. Focus: ASC 606 revenue recognition, Damodaran sector margins, Damodaran debt sector fundamentals.",
    "Governance Analyst needs relevant benchmarks and accounting guidance. Focus: ASC 606 revenue recognition, Damodaran sector margins, Damodaran debt sector fundamentals.",
    "Business & Ops Analyst needs relevant benchmarks and accounting guidance. Focus: ASC 606 revenue recognition, Damodaran sector margins, Damodaran debt sector fundamentals."
]

for q in queries:
    print(f"\n--- Query: {q[:100]}... ---")
    context = get_council_context(q)
    if context:
        print(f"✅ Found context! ({len(context)} chars)")
        print(context[:500] + "...")
    else:
        print("❌ No context found.")
