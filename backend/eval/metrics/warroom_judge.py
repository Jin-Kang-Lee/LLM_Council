"""
War Room LLM-as-Judge Evaluator

Uses OpenAI GPT-4o to score the quality of the multi-agent War Room discussion.

Bias mitigations applied:
  - Agent names are anonymised (Agent A / B / C) so the judge cannot
    favour a role by its title (e.g. "Risk Analyst sounds authoritative").
  - The rubric explicitly penalises verbosity bias and positional bias.
  - Scores are anchored to concrete behavioural descriptors (0 / 5 / 10)
    so the judge cannot drift into vague mid-range scoring.
  - The judge is instructed NOT to compare agents against each other —
    only to assess the discussion as a whole system.
  - Temperature is set to 0 for reproducibility.
"""

from __future__ import annotations

import json
import os
import random
from typing import Any

_JUDGE_SYSTEM = """\
You are a rigorous evaluator of multi-agent financial analysis discussions.
Your job is to score the OVERALL DISCUSSION — not individual agents.

ANTI-BIAS RULES — read carefully before scoring:
1. Do NOT reward verbosity. A concise, evidence-backed point scores higher
   than a long, vague one.
2. Do NOT favour the first or last speaker. Ignore message order when scoring.
3. Agent names have been anonymised (Agent A, B, C). Do not infer roles from
   content and use that to inflate or deflate scores.
4. Do NOT assume any financial viewpoint (bullish/bearish/cautious) is
   inherently more credible. Score the quality of reasoning, not the conclusion.
5. Score only what is present in the transcript. Do not reward potential.
"""

_JUDGE_PROMPT = """\
Score the following War Room discussion transcript on five dimensions.
Each dimension is scored 0–10 using the anchors provided.

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

# Maximum transcript characters sent to the judge (cost + context control)
MAX_TRANSCRIPT_CHARS = 12_000


def _anonymise_transcript(messages: list[dict]) -> str:
    """
    Replace real agent names with neutral labels (Agent A, B, C …) and
    shuffle the label assignment randomly so the judge cannot learn that
    e.g. 'Agent A' is always the Risk Analyst across runs.
    """
    names = list({m["agent"] for m in messages})
    random.shuffle(names)
    label_map = {name: f"Agent {chr(65 + i)}" for i, name in enumerate(names)}

    lines: list[str] = []
    for msg in messages:
        label = label_map[msg["agent"]]
        round_tag = f"[Round {msg['round']}]"
        lines.append(f"{label} {round_tag}:\n{msg['content']}")

    return "\n\n".join(lines)


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... [transcript truncated]"


def _parse_judge_json(raw: str) -> dict | None:
    raw = raw.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


def _call_openai(prompt: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _JUDGE_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""


def evaluate_warroom_discussion(outputs: dict, openai_key: str | None) -> dict[str, Any]:
    """
    Score the War Room discussion using GPT-4o as an impartial judge.

    Args:
        outputs:    agent_outputs dict from the pipeline (must contain 'discussion').
        openai_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.

    Returns a dict with per-dimension scores, rationales, and a summary.
    """
    key = openai_key or os.getenv("OPENAI_API_KEY", "")
    if not key:
        return {
            "skipped": True,
            "reason": "No OpenAI API key provided. Set OPENAI_API_KEY or pass --openai_key.",
        }

    messages: list[dict] = outputs.get("discussion", [])
    if not messages:
        return {"skipped": True, "reason": "No discussion messages found in outputs."}

    transcript = _anonymise_transcript(messages)
    transcript = _truncate(transcript, MAX_TRANSCRIPT_CHARS)

    prompt = _JUDGE_PROMPT.format(transcript=transcript)

    try:
        raw = _call_openai(prompt, key)
    except Exception as e:
        return {"skipped": True, "reason": f"OpenAI API error: {str(e)}"}

    parsed = _parse_judge_json(raw)
    if not parsed:
        return {
            "skipped": True,
            "reason": "Judge returned invalid JSON.",
            "raw_response": raw[:500],
        }

    score_keys = [
        "argument_quality",
        "reasoning_diversity",
        "engagement_quality",
        "conflict_resolution",
        "discussion_utility",
    ]

    # Recompute overall_score ourselves to guard against model arithmetic errors
    scores = [int(parsed.get(k, 0)) for k in score_keys]
    overall = round(sum(scores) / len(scores), 2)

    return {
        **{k: parsed.get(k) for k in score_keys},
        **{f"{k}_rationale": parsed.get(f"{k}_rationale", "") for k in score_keys},
        "overall_score": overall,
        "key_strength": parsed.get("key_strength", ""),
        "key_weakness": parsed.get("key_weakness", ""),
        "_summary": {
            "overall_score": overall,
            "num_messages": len(messages),
            "num_rounds": max((m["round"] for m in messages), default=0),
        },
    }
