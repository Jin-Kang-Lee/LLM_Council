import os
import json
import glob
import matplotlib.pyplot as plt

def get_latest_results_file(results_dir="eval/results"):
    """Finds the most recently created JSON file in the results directory."""
    if not os.path.exists(results_dir):
        print(f"Directory {results_dir} does not exist.")
        return None
    
    files = glob.glob(os.path.join(results_dir, "eval_*.json"))
    if not files:
        print(f"No evaluation JSON files found in {results_dir}")
        return None
        
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def visualize_rag_faithfulness():
    latest_file = get_latest_results_file()
    if not latest_file:
        return
        
    print(f"\n📊 Reading data from: {latest_file}\n")
    
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Initialize counters for each agent
    agent_stats = {
        "risk": {"passed": 0, "total": 0},
        "business_ops": {"passed": 0, "total": 0},
        "governance": {"passed": 0, "total": 0}
    }
    
    overall_passed = 0
    overall_total = 0

    test_cases = data.get("test_cases", [])
    
    # Check if this isn't the new format
    if not test_cases:
        print("Data format not recognized or no test cases run.")
        return

    for case in test_cases:
        evals = case.get("evaluations", {})
        rag_eval = evals.get("rag_faithfulness", {})
        
        # Count passes/fails for each agent
        for agent_name in agent_stats.keys():
            agent_result = rag_eval.get(agent_name, {})
            if agent_result and not agent_result.get("skipped", False):
                agent_stats[agent_name]["total"] += 1
                overall_total += 1
                if agent_result.get("faithful") is True:
                    agent_stats[agent_name]["passed"] += 1
                    overall_passed += 1

    # Print Numbers Summary to Console
    print("=" * 50)
    print(" 📈 RAG FAITHFULNESS SUMMARY (NUMBERS) ")
    print("=" * 50)
    print(f"Overall Script Execution: {overall_total} Evaluations Completed.")
    print(f"Overall Pass Rate: {overall_passed}/{overall_total} ({(overall_passed/max(1, overall_total))*100:.1f}%)\n")
    
    labels = []
    pass_rates = []
    colors = ['#ff595e', '#ffca3a', '#8ac926'] # Red, Yellow, Green
    
    for idx, (agent, stats) in enumerate(agent_stats.items()):
        total = stats['total']
        passed = stats['passed']
        if total > 0:
            rate = (passed / total) * 100
            print(f"➤ {agent.replace('_', ' ').title()}: {passed}/{total} instances were perfectly faithful ({rate:.0f}%)")
            labels.append(agent.replace('_', ' ').title())
            pass_rates.append(rate)

    print("=" * 50 + "\n")

    # Generate Matplotlib Graph
    if not labels:
        print("No RAG Faithfulness data found to plot. Did you run the --tests=rag_faithfulness command?")
        return
        
    plt.figure(figsize=(8, 6))
    bars = plt.bar(labels, pass_rates, color=colors[:len(labels)])
    
    # Add styling and labels
    plt.ylim(0, 110)
    plt.ylabel('Pass Rate (%)', fontsize=12, fontweight='bold')
    plt.title('Agent Fact-Checking (RAG Faithfulness)', fontsize=14, fontweight='bold')
    
    # Add text percentages on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')

    # Save to file AND show interactively
    save_path = "eval/results/eval_graph.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"📷 Graph successfully saved as an image to: {save_path}")
    
    # This will open the graphical window on your computer
    print("Pop-up graph opening window now... (Close the window to end the script)")
    plt.show()

if __name__ == "__main__":
    visualize_rag_faithfulness()
