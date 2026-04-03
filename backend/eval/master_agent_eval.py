import sys
import os
import json
import asyncio
import traceback
import ollama
import re

# ── Setup ─────────────────────────────────────────────────────────────── #
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
sys.path.append(PROJECT_ROOT)

from agents import MasterAgent

DATA_DIR = os.path.join(CURRENT_DIR, "master_agent_eval", "data")
RESULTS_DIR = os.path.join(CURRENT_DIR, "master_agent_eval", "results")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


# ── Extractor and Judge Prompts ────────────────────────────────────────────── #

_EXTRACTION_PROMPT = """You are a data extraction assistant. Given a Markdown investment report, extract the following fields and return ONLY a valid JSON object — no explanation, no markdown fences.

Fields to extract:
- risk_level: exactly "Low", "Medium", or "High"
- primary_risks: list of strings naming the main risks identified (3-5 items)
- management_confidence: exactly "Low", "Medium", or "High"
- market_outlook: one of "Bearish", "Neutral", "Bullish"
- governance_risk: exactly "Low", "Medium", or "High"
- points_of_agreement: list of strings summarising consensus points (2-4 items)
- final_recommendation: the investment recommendation as a short string

Only return the JSON.
Report to extract from:
---
{report}
---
"""

_JUDGE_PROMPT = """You are an expert financial report quality evaluator.

You will be given:
1. ANALYST INPUTS: The raw outputs from specialist analysts...
2. CONSOLIDATED REPORT: A Master Agent's final Markdown investment report...

Your task: Score the quality of synthesis on the following 4 axes.
Return ONLY a valid JSON object with integer scores 0-10 and a rationale for each.

SCORING RUBRIC:
1. conflict_resolution (0-10)
2. completeness (0-10)
3. factual_grounding (0-10)
4. narrative_coherence (0-10)

Return this exact JSON shape:
{{
  "conflict_resolution": <int>,
  "conflict_resolution_rationale": "<str>",
  "completeness": <int>,
  "completeness_rationale": "<str>",
  "factual_grounding": <int>,
  "factual_grounding_rationale": "<str>",
  "narrative_coherence": <int>,
  "narrative_coherence_rationale": "<str>"
}}

ANALYST INPUTS:
{analyst_inputs}

CONSOLIDATED REPORT:
{consolidated_report}
"""

async def extract_from_markdown_ollama(report: str) -> dict | None:
    prompt = _EXTRACTION_PROMPT.format(report=report[:6000])
    try:
        response = ollama.chat(
            model='llama3.1',
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.0}
        )
        raw = response['message']['content'] or ""
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(raw)
    except Exception as e:
        print(f"     ❌ Extraction error: {e}")
        return None

# ── Inlined Metric Scorers ────────────────────────────────────────────────── #

def _check_categorical(actual_value: str, expected_value: str) -> dict:
    match = actual_value.strip().lower() == expected_value.strip().lower()
    return {"expected": expected_value, "actual": actual_value, "match": match}

def _compute_precision_recall_f1(pred_items, gt_items, pred_key, gt_key) -> dict:
    gt_labels = [item.get(gt_key, "").lower() for item in gt_items]
    pred_labels = [item.get(pred_key, "").lower() for item in pred_items]

    def _labels_match(pred: str, gt: str) -> bool:
        gt_w = [w for w in gt.split() if len(w) >= 4]
        pred_w = [w for w in pred.split() if len(w) >= 4]
        return any(w in pred for w in gt_w) or any(w in gt for w in pred_w)

    gt_matched = [lbl for lbl in gt_labels if any(_labels_match(pred, lbl) for pred in pred_labels)]
    pred_extra = [lbl for lbl in pred_labels if not any(_labels_match(lbl, gt) for gt in gt_labels)]

    tp = len(gt_matched)
    fn = len(gt_labels) - tp
    fp = len(pred_extra)

    precision = round(tp / (tp + fp), 3) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 3) if (tp + fn) > 0 else 0.0
    f1 = round(2 * precision * recall / (precision + recall), 3) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


def _parse_ollama_json(raw: str) -> dict | None:
    try:
        return json.loads(raw)
    except:
        pass
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except:
            pass
    first, last = raw.find("{"), raw.rfind("}")
    if first != -1 and last > first:
        try:
            return json.loads(raw[first: last + 1])
        except:
            pass
    return None

def score_with_judge_ollama(case_data: dict, report: str, model: str = "llama3.1") -> dict | None:
    analyst_inputs = json.dumps({
        "analyst_risk": case_data.get("analyst_risk", {}),
        "analyst_sentiment": case_data.get("analyst_sentiment", {}),
        "analyst_governance": case_data.get("analyst_governance", {}),
        "discussion_transcript": case_data.get("discussion_transcript", [])
    }, indent=2)

    prompt = _JUDGE_PROMPT.format(analyst_inputs=analyst_inputs[:4000], consolidated_report=report[:3000])

    try:
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], options={"temperature": 0.0})
        parsed = _parse_ollama_json(response["message"]["content"] or "")
        if not parsed: return None

        score_keys = ["conflict_resolution", "completeness", "factual_grounding", "narrative_coherence"]
        scores = {k: int(parsed[k]) for k in score_keys if k in parsed}
        if len(scores) < 4: return None
        return {**scores, "judge_avg": round(sum(scores.values()) / len(scores), 2)}
    except Exception as e:
        print(f"     ⚠️  Judge error: {e}")
        return None

# ── Strategy definitions ──────────────────────────────────────────────────── #
STRATEGIES = {
    "baseline": None,
    "cot": (
        "Before writing the final report, first reason step-by-step:\n"
        "1. List the major points of CONSENSUS across all analysts.\n"
        "2. List the key DISAGREEMENTS found in the transcript.\n"
        "3. Weigh the evidence and decide on a resolution for each conflict.\n"
        "4. Only then generate the full structured report.\n"
        "Produce the complete report as your final output."
    ),
    "few_shot": (
        "Here is an example of how to synthesise a split panel:\n\n"
        "--- EXAMPLE ---\n"
        "Scenario: Risk analyst flags heavy CapEx risk; Sentiment analyst argues the spend is justified.\n"
        "Resolution in report: 'Capital expenditure poses a liquidity risk; however, revenue acceleration supports a Medium overall risk rating.'\n"
        "--- END EXAMPLE ---\n\n"
        "Apply this discipline to the current data. Produce a complete professional report."
    ),
}

def load_dataset(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_context(case: dict) -> str:
    return f"## RISK ANALYST'S ASSESSMENT\n{json.dumps(case.get('analyst_risk', {}), indent=2)}\n\n---\n\n## SENTIMENT ANALYST'S ASSESSMENT\n{json.dumps(case.get('analyst_sentiment', {}), indent=2)}\n\n---\n\n## ANALYST DISCUSSION TRANSCRIPT\n{json.dumps(case.get('discussion_transcript', []), indent=2)}"

def compute_metrics(extracted: dict, ground_truth: dict) -> dict:
    gt_risk   = ground_truth.get("risk_assessment", {})
    risk_cat = _check_categorical(extracted.get("risk_level", ""), gt_risk.get("risk_level", ""))
    pred_risks = [{"factor": r} for r in extracted.get("primary_risks", [])]
    gt_risks   = [{"factor": r} for r in gt_risk.get("primary_risks", [])]
    risk_prf = _compute_precision_recall_f1(pred_risks, gt_risks, "factor", "factor")
    return {
        "risk_level_match": risk_cat["match"],
        "risk_f1": risk_prf["f1"],
    }

async def run_benchmark():
    if not os.path.exists(DATA_DIR) or not os.listdir(DATA_DIR):
        print(f"❌ Cannot find data in {DATA_DIR}! Please place the case files here.")
        return []

    # Dynamically load all case files from the data directory
    case_files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    
    agent = MasterAgent()
    all_results = []

    print("\n" + "=" * 65)
    print(" MASTER AGENT BENCHMARK (LOCAL OLLAMA)")
    print(f" Detected {len(case_files)} cases in data folder.")
    print("=" * 65)

    for case_filename in case_files:
        case_id = os.path.splitext(case_filename)[0]
        case_path = os.path.join(DATA_DIR, case_filename)
        
        try:
            case_data = load_dataset(case_path)
        except Exception as e:
            print(f"⚠️ Skipping {case_filename}: Not a valid JSON format ({e})")
            continue
            
        gt = case_data.get("ground_truth_json")
        if not gt:
            print(f"⚠️ Skipping {case_filename}: Missing 'ground_truth_json'")
            continue

        context = build_context(case_data)
        print(f"\n  CASE: {case_id}")
        for strategy_name, instructions in STRATEGIES.items():
            print(f"\n  🚀 Strategy: {strategy_name.upper()}")
            try:
                if strategy_name == "baseline":
                    raw_report = await agent.consolidate(
                        original_content="",
                        risk_analysis=json.dumps(case_data.get("analyst_risk", {}), indent=2),
                        sentiment_analysis=json.dumps(case_data.get("analyst_sentiment", {}), indent=2),
                        governance_analysis=json.dumps(case_data.get("analyst_governance", {}), indent=2),
                        research_analysis="",
                        discussion_transcript=json.dumps(case_data.get("discussion_transcript", []), indent=2)
                    )
                else:
                    raw_report = await agent.generate(context, instructions)

                print(f"     ✅ Report generated ({len(raw_report)} chars)")
                extracted = await extract_from_markdown_ollama(raw_report)
                if not extracted:
                    all_results.append({"case_id": case_id, "strategy": strategy_name, "extracted": False})
                    continue

                metrics = compute_metrics(extracted, gt)
                judge_scores = score_with_judge_ollama(case_data, raw_report) or {}
                
                all_results.append({
                    "case_id": case_id,
                    "strategy": strategy_name,
                    "extracted": True,
                    **metrics,
                    **judge_scores,
                })
            except Exception:
                print(f"     🧨 Error: {traceback.format_exc()}")

    # Table
    print(f"\n{'=' * 75}\n{'CASE':<22} {'STRATEGY':<12} {'RISK ACC':>9} {'RISK F1':>8} {'JUDGE':>7}\n" + "-" * 75)
    for r in all_results:
        if r.get("extracted"):
            print(f"{r['case_id']:<22} {r['strategy']:<12} {float(r['risk_level_match']):>9.2f} {r.get('risk_f1', 0):>8.2f} {r.get('judge_avg', float('nan')):>7.1f}")

    results_file = os.path.join(RESULTS_DIR, "last_run.json")
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n✅ Results saved to {results_file}")
    return all_results

if __name__ == "__main__":
    asyncio.run(run_benchmark())
