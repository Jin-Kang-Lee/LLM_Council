"""
Generates ready-to-paste LLM judge prompt .txt files from war room capture JSONs.
One .txt per TC — paste the entire contents into any chatbox (ChatGPT, Claude, etc.)

Usage:
    python eval/generate_judge_prompts.py
    python eval/generate_judge_prompts.py --input eval/war_room_results --output eval/judge_prompts
"""

import argparse
import json
import os
import random
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = CURRENT_DIR / "war_room_results"
DEFAULT_OUTPUT = CURRENT_DIR / "judge_prompts"

PROMPT_TEMPLATE = """\
You are a rigorous evaluator of multi-agent financial analysis discussions.
Your job is to score the OVERALL DISCUSSION — not individual agents.

ANTI-BIAS RULES — read carefully before scoring:
1. Do NOT reward verbosity. A concise, evidence-backed point scores higher than a long, vague one.
2. Do NOT favour the first or last speaker. Ignore message order when scoring.
3. Agent names have been anonymised (Agent A, B, C). Do not infer roles from content and use that to inflate or deflate scores.
4. Do NOT assume any financial viewpoint (bullish/bearish/cautious) is inherently more credible. Score the quality of reasoning, not the conclusion.
5. Score only what is present in the transcript. Do not reward potential.

---

Score the following War Room discussion transcript on five dimensions.
Each dimension is scored 0-10 using the anchors provided.

--- TRANSCRIPT ---
{transcript}
--- END TRANSCRIPT ---

SCORING DIMENSIONS AND ANCHORS:

1. argument_quality (0-10)
   Are claims backed by specific data, figures, or quotes from the report?
   0  = All claims are vague assertions with no supporting evidence.
   5  = Some claims cite specific numbers; others are unsubstantiated.
   10 = Every substantive claim is tied to a specific data point or direct quote.

2. reasoning_diversity (0-10)
   Do the agents surface genuinely different analytical perspectives?
   0  = Agents repeat the same points; no unique viewpoints raised.
   5  = Some differentiation, but significant overlap in findings.
   10 = Each agent raises distinct, non-overlapping insights that collectively
        cover risk, operations, and governance without redundancy.

3. engagement_quality (0-10)
   Do agents actually respond to each other's specific arguments?
   0  = Each agent monologues; no direct responses to prior statements.
   5  = Agents acknowledge prior points but do not challenge or build on them.
   10 = Agents explicitly reference, challenge, or build on each other's
        specific claims, creating a genuine back-and-forth.

4. conflict_resolution (0-10)
   When agents disagree, is the disagreement substantive and resolved?
   0  = No disagreements surfaced despite differing evidence.
   5  = Disagreements are named but left open with no reasoning.
   10 = Key disagreements are clearly identified and resolved with explicit
        reasoning that references evidence from the report.

5. discussion_utility (0-10)
   Does the discussion produce insights beyond the individual analyses?
   0  = The discussion adds nothing beyond what the individual analyses said.
   5  = One or two new synthesis points emerge from the debate.
   10 = The discussion changes or meaningfully sharpens the analytical
        conclusion in a way that individual analyses could not.

Return ONLY this exact JSON — no explanation, no markdown fences:
{{
  "argument_quality": <int 0-10>,
  "argument_quality_rationale": "<max 2 sentences>",
  "reasoning_diversity": <int 0-10>,
  "reasoning_diversity_rationale": "<max 2 sentences>",
  "engagement_quality": <int 0-10>,
  "engagement_quality_rationale": "<max 2 sentences>",
  "conflict_resolution": <int 0-10>,
  "conflict_resolution_rationale": "<max 2 sentences>",
  "discussion_utility": <int 0-10>,
  "discussion_utility_rationale": "<max 2 sentences>",
  "overall_score": <float, mean of the five scores rounded to 2 dp>,
  "key_strength": "<one sentence>",
  "key_weakness": "<one sentence>"
}}
"""


def anonymise(messages: list[dict]) -> str:
    names = list({m["agent"] for m in messages})
    random.shuffle(names)
    label_map = {name: f"Agent {chr(65 + i)}" for i, name in enumerate(names)}

    lines = []
    for msg in messages:
        label = label_map[msg["agent"]]
        lines.append(f"{label} [Round {msg['round']}]:\n{msg['content']}")

    return "\n\n".join(lines)


def generate(input_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(input_dir.glob("*.json"))

    # Skip previously saved score files
    files = [f for f in files if not f.stem.startswith("judge_scores")]

    if not files:
        print(f"No capture JSON files found in {input_dir}")
        return

    print(f"Found {len(files)} capture file(s)\n")

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            capture = json.load(f)

        test_id = capture.get("test_id", path.stem)
        description = capture.get("description", "")
        messages = capture.get("discussion", [])

        if not messages:
            print(f"  {test_id}: no discussion messages — skipping")
            continue

        transcript = anonymise(messages)
        prompt = PROMPT_TEMPLATE.format(transcript=transcript)

        header = (
            f"=== WAR ROOM JUDGE PROMPT ===\n"
            f"Test Case : {test_id}\n"
            f"Description: {description}\n"
            f"Messages  : {len(messages)} across {max(m['round'] for m in messages)} rounds\n"
            f"{'=' * 60}\n\n"
        )

        out_path = output_dir / f"{test_id}_judge_prompt.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(header + prompt)

        print(f"  Written: {out_path.name}  ({len(messages)} messages)")

    print(f"\nDone. Files saved to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    random.seed()  # Fresh shuffle each run
    generate(Path(args.input), Path(args.output))
