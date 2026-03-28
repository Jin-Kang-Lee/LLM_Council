import os
import json
import glob
import matplotlib.pyplot as plt

def get_latest_results_file(results_dir="eval/results"):
    if not os.path.exists(results_dir): return None
    files = glob.glob(os.path.join(results_dir, "eval_*.json"))
    if not files: return None
    return max(files, key=os.path.getmtime)

def plot_reference_metrics():
    latest_file = get_latest_results_file()
    if not latest_file:
        print("No evaluation JSON files found.")
        return
        
    print(f"\n📊 Reading REFERENCE BASED data from: {latest_file}\n")
    
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Initialize stats per agent for different categories
    agent_stats = {
        "risk": {"data_passed": 0, "data_total": 0, "rag_passed": 0, "rag_total": 0, "tool_passed": 0, "tool_total": 0},
        "business_ops": {"data_passed": 0, "data_total": 0, "rag_passed": 0, "rag_total": 0, "tool_passed": 0, "tool_total": 0},
        "governance": {"data_passed": 0, "data_total": 0, "rag_passed": 0, "rag_total": 0, "tool_passed": 0, "tool_total": 0}
    }

    test_cases = data.get("test_cases", [])
    for case in test_cases:
        evals = case.get("evaluations", {})
        
        # 1. Reference-Based (Data Accuracy)
        ref_eval = evals.get("reference_based", {})
        for agent in agent_stats:
            res = ref_eval.get(agent, {})
            if "skipped" not in res:
                for k, v in res.items():
                    if isinstance(v, dict):
                        if "match" in v:
                            agent_stats[agent]["data_total"] += 1
                            if v["match"]: agent_stats[agent]["data_passed"] += 1
                        elif "found" in v and "total_expected" in v:
                            agent_stats[agent]["data_total"] += v["total_expected"]
                            agent_stats[agent]["data_passed"] += v["found"]
        
        # 2. RAG Retrieval
        rag_eval = evals.get("rag_retrieval", {})
        for agent in agent_stats:
            res = rag_eval.get(agent, {})
            if res:
                # Use source hit rate and keyword hit rate
                agent_stats[agent]["rag_total"] += 2 
                if res.get("source_hit_rate", 0) > 0: agent_stats[agent]["rag_passed"] += 1
                if res.get("keyword_hit_rate", 0) > 0.5: agent_stats[agent]["rag_passed"] += 1
        
        # 3. Tool Faithfulness
        tool_eval = evals.get("tool_faithfulness", {})
        for agent in agent_stats:
            res = tool_eval.get(agent, {})
            if res:
                agent_stats[agent]["tool_total"] += 1
                invoc = res.get("tool_invocation", {})
                if invoc.get("passed"): agent_stats[agent]["tool_passed"] += 1

    print("=" * 50)
    print(" 📈 AGENT ECOSYSTEM SCORECARD (RAG & TOOLS) ")
    print("=" * 50)
    
    agents = ["Risk", "Business Ops", "Governance"]
    data_acc = []
    rag_acc = []
    tool_acc = []
    
    for key in ["risk", "business_ops", "governance"]:
        stats = agent_stats[key]
        d_rate = (stats["data_passed"] / stats["data_total"] * 100) if stats["data_total"] > 0 else 0
        r_rate = (stats["rag_passed"] / stats["rag_total"] * 100) if stats["rag_total"] > 0 else 0
        t_rate = (stats["tool_passed"] / stats["tool_total"] * 100) if stats["tool_total"] > 0 else 0
        
        print(f"➤ {key.replace('_',' ').title()}:")
        print(f"   - Data Accuracy: {d_rate:.0f}% ({stats['data_passed']}/{stats['data_total']})")
        print(f"   - RAG Retrieval: {r_rate:.0f}%")
        print(f"   - Tool Success:  {t_rate:.0f}%")
        
        data_acc.append(d_rate)
        rag_acc.append(r_rate)
        tool_acc.append(t_rate)

    import numpy as np
    x = np.arange(len(agents))
    width = 0.25
    
    plt.figure(figsize=(12, 7))
    plt.bar(x - width, data_acc, width, label='Data Accuracy', color='#ff595e')
    plt.bar(x, rag_acc, width, label='RAG Retrieval', color='#8ac926')
    plt.bar(x + width, tool_acc, width, label='Tool Success', color='#1982c4')
    
    plt.xlabel('Agents', fontsize=12, fontweight='bold')
    plt.ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
    plt.title('Agent Performance: RAG, Tools & Accuracy', fontsize=15, fontweight='bold')
    plt.xticks(x, agents)
    plt.ylim(0, 110)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    save_path = "eval/results/eval_accuracy_graph.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n📷 Grouped chart saved to: {save_path}")
    plt.show()

if __name__ == "__main__":
    plot_reference_metrics()
