import os
import json
import matplotlib.pyplot as plt
import numpy as np
import glob

def visualize_rag():
    # Find latest eval file
    files = glob.glob("eval/results/eval_*.json")
    if not files:
        print("No evaluation files found.")
        return
    latest = max(files, key=os.path.getctime)
    print(f"📊 Reading RAG data from: {latest}")

    with open(latest, "r") as f:
        data = json.load(f)

    agents = ["risk", "business_ops", "governance"]
    metrics = ["Source Hit Rate", "Keyword Hit Rate", "Required Coverage"]
    
    # Aggregate data
    results = {a: [] for a in agents}
    for case in data["test_cases"]:
        rag_eval = case["evaluations"].get("rag_retrieval", {})
        for a in agents:
            a_eval = rag_eval.get(a, {})
            results[a].append([
                a_eval.get("source_hit_rate", 0),
                a_eval.get("keyword_hit_rate", 0),
                a_eval.get("required_coverage_rate", 0)
            ])

    # Average across test cases
    avg_results = {}
    for a in agents:
        avg_results[a] = np.mean(results[a], axis=0) * 100

    # Plot
    x = np.arange(len(metrics))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 6))

    for i, a in enumerate(agents):
        ax.bar(x + i*width, avg_results[a], width, label=a.replace("_", " ").title())

    ax.set_ylabel("Success Rate (%)")
    ax.set_title("RAG Retrieval Performance by Agent")
    ax.set_xticks(x + width)
    ax.set_xticklabels(metrics)
    ax.legend()
    ax.set_ylim(0, 105)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    output_path = "eval/results/rag_performance.png"
    plt.savefig(output_path)
    print(f"📷 RAG performance chart saved to: {output_path}")

if __name__ == "__main__":
    visualize_rag()
