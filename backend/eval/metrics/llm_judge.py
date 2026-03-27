"""
War Room Evaluator (LLM Judge)

Uses a local Ollama LLM to evaluate the quality of the multi-agent debate (War Room).
Specifically looks at how well Risk, Business Ops, and Governance agents interacted.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

OLLAMA_URL = f"{OLLAMA_BASE_URL}/v1/chat/completions"
JUDGE_MODEL = os.getenv("EVAL_JUDGE_MODEL", OLLAMA_MODEL)


def _call_ollama_judge(messages: list[dict]) -> dict | None:
    payload = {
        "model": JUDGE_MODEL,
        "messages": messages,
        "temperature": 0.0,
    }

    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            raw = result["choices"][0]["message"]["content"]
            # Extract JSON, since Ollama/Qwen may wrap it in markdown fences
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(raw[start : end + 1])
            return json.loads(raw)
    except Exception as e:
        return {"error": str(e)}



def evaluate_individual_agent(agent_name: str, agent_output: str, original_report: str) -> dict[str, Any]:
    """
    Evaluates a single agent's overall quality and accuracy without needing any Chromadb RAG context.
    """
    if not agent_output:
        return {"skipped": True, "reason": "No agent output provided"}

    system_prompt = (
        f"You are an expert Chief Risk Officer evaluating an AI '{agent_name}'.\n"
        "Read the original Earnings Report, then read the agent's analysis.\n\n"
        "Criteria to evaluate:\n"
        "1. Accuracy: Did the agent accurately extract the numbers from the report?\n"
        "2. Insight: Did the agent provide professional, meaningful insights or just restate the text?\n"
        "3. Completeness: Did the agent miss any glaring massive risks or details?\n\n"
        "Output a JSON object with EXACTLY this structure (no markdown fences, raw JSON only):\n"
        "{\n"
        '  "score": 0.0 to 10.0,\n'
        '  "critique": "A short paragraph explaining the score.",\n'
        '  "hallucinations_found": true or false\n'
        "}"
    )

    user_prompt = (
        f"ORIGINAL EARNINGS REPORT:\n{original_report}\n\n"
        f"---\n\n{agent_name.upper()} ANALYSIS OUTPUT:\n{agent_output}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    judge_result = _call_ollama_judge(messages)

    if judge_result and "error" not in judge_result:
        judge_result["status"] = "evaluated"
        return judge_result
    else:
        return {
            "skipped": True,
            "reason": judge_result.get("error", "Unknown error") if judge_result else "Null response"
        }

def evaluate_warroom_discussion(agent_outputs: dict) -> dict[str, Any]:
    """
    Evaluates the 'discussion' array from the agent outputs.
    """
    discussion = agent_outputs.get("discussion", [])
    if not discussion:
        return {"skipped": True, "reason": "No discussion transcript found."}

    # Format transcript
    transcript = ""
    for msg in discussion:
        agent = msg.get("agent", "Unknown")
        round_num = msg.get("round", "?")
        content = msg.get("content", "")
        transcript += f"[{agent} - Round {round_num}]:\n{content}\n\n"

    system_prompt = (
        "You are an expert panel judge evaluating an AI Multi-Agent debate (the 'War Room').\n"
        "Your goal is to assess the quality of the interactions between the Risk Analyst, "
        "Business & Ops Analyst, and Governance Analyst.\n\n"
        "Criteria to evaluate:\n"
        "1. Constructiveness: Did agents build on each other's points or just talk past each other?\n"
        "2. Evidence-based: Did they cite specific numbers/facts to back up their challenges?\n"
        "3. Resolution: Did they reach a logical conclusion or expose a genuine disagreement?\n\n"
        "Output a JSON object with EXACTLY this structure (no markdown fences, raw JSON only):\n"
        "{\n"
        '  "overall_score": 0.0 to 10.0,\n'
        '  "critique": "A short paragraph explaining the score",\n'
        '  "best_argument": "Describe the most compelling point made and by whom",\n'
        '  "missed_opportunities": ["list", "of", "missed", "points"]\n'
        "}"
    )

    user_prompt = f"DEBATE TRANSCRIPT:\n{transcript}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    judge_result = _call_ollama_judge(messages)

    if judge_result and "error" not in judge_result:
        judge_result["status"] = "evaluated"
        return judge_result
    else:
        return {
            "skipped": True,
            "reason": judge_result.get("error", "Unknown error") if judge_result else "Null response"
        }
