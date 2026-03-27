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

    # Initialize accuracy stats per agent
    agent_stats = {
        "risk": {"passed": 0, "total": 0},
        "business_ops": {"passed": 0, "total": 0},
        "governance": {"passed": 0, "total": 0}
    }

    overall_passed = 0
    overall_total = 0

    test_cases = data.get("test_cases", [])
    if not test_cases:
        print("Data format not recognized.")
        return

    # Extract accuracy from reference_based
    for case in test_cases:
        evals = case.get("evaluations", {})
        ref_eval = evals.get("reference_based", {})
        
        for agent_name in agent_stats.keys():
            agent_result = ref_eval.get(agent_name, {})
            if "skipped" in agent_result: continue
            
            # Count categorical match booleans
            for key, val in agent_result.items():
                if isinstance(val, dict):
                    if "match" in val:
                        agent_stats[agent_name]["total"] += 1
                        overall_total += 1
                        if val["match"]:
                            agent_stats[agent_name]["passed"] += 1
                            overall_passed += 1
                    # Extract keyword recall fractions
                    elif "found" in val and "total_expected" in val:
                        agent_stats[agent_name]["total"] += val["total_expected"]
                        overall_total += val["total_expected"]
                        agent_stats[agent_name]["passed"] += val["found"]
                        overall_passed += val["found"]

    print("=" * 50)
    print(" 📈 STRICT DATA ACCURACY SCORES (NO RAG) ")
    print("=" * 50)
    print(f"Overall Checks Performed: {overall_total}")
    if overall_total > 0:
        print(f"Overall Ecosystem Accuracy: {overall_passed}/{overall_total} ({(overall_passed/overall_total)*100:.1f}%)\n")
    
    labels = []
    pass_rates = []
    colors = ['#ff595e', '#ffca3a', '#8ac926']
    
    for idx, (agent, stats) in enumerate(agent_stats.items()):
        total = stats['total']
        passed = stats['passed']
        if total > 0:
            rate = (passed / total) * 100
            print(f"➤ {agent.replace('_', ' ').title()}: Passed {passed}/{total} data-point checks ({rate:.0f}% Accuracy)")
            labels.append(agent.replace('_', ' ').title())
            pass_rates.append(rate)

    print("=" * 50 + "\n")

    if not labels:
        print("No Reference-Based data found to plot. Run test using: --tests=reference")
        return
        
    plt.figure(figsize=(8, 6))
    bars = plt.bar(labels, pass_rates, color=colors[:len(labels)])
    
    plt.ylim(0, 110)
    plt.ylabel('Strict Data Accuracy (%)', fontsize=12, fontweight='bold')
    plt.title('Agent Fact-Extraction Performance (Non-RAG)', fontsize=14, fontweight='bold')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')

    save_path = "eval/results/eval_accuracy_graph.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"📷 Graph successfully saved to: {save_path}")
    print("Opening Data Accuracy graph...")
    plt.show()

if __name__ == "__main__":
    plot_reference_metrics()
