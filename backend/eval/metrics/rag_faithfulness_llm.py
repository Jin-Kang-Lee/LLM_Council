"""
RAG Faithfulness (LLM Judge)

Uses a local Ollama LLM to verify that the agent's answer is supported
by the retrieved context. Evaluates Risk, Business Ops, and Governance agents.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from config import OLLAMA_BASE_URL, OLLAMA_MODEL

OLLAMA_URL = f"{OLLAMA_BASE_URL}/v1/chat/completions"
JUDGE_MODEL = os.getenv("EVAL_JUDGE_MODEL", OLLAMA_MODEL)

MAX_CONTEXT_CHARS = 6000
MAX_ANSWER_CHARS = 2000

# Specific agents to evaluate
TARGET_AGENTS = {"risk", "business_ops", "governance"}


def _truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated]"


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = text[start : end + 1]
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _build_messages(answer: str, context: str) -> list[dict]:
    system_prompt = (
        "You are a strict, objective fact-checker. Decide whether the provided ANSWER is "
        "fully supported by the provided CONTEXT.\n"
        "If any claim in the ANSWER is not explicitly supported by the CONTEXT, mark faithful=false.\n"
        "Do not assume missing information. Your output MUST be a strict JSON object matching this schema:\n"
        '{"faithful": true or false, "score": 0.0 to 1.0, "unsupported_claims": ["list of strings"], "notes": "brief explanation"}'
    )
    user_prompt = (
        f"CONTEXT:\n{context}\n\n"
        f"ANSWER:\n{answer}\n\n"
        "Respond ONLY with a JSON object, no markdown, no commentary."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


def _call_ollama_judge(messages: list[dict]) -> str:
    payload = {
        "model": JUDGE_MODEL,
        "messages": messages,
        "temperature": 0.0,
    }

    with httpx.Client(timeout=300.0) as client:
        response = client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


def _judge_faithfulness(answer: str, context: str) -> dict[str, Any]:
    trimmed_answer = _truncate(answer, MAX_ANSWER_CHARS)
    trimmed_context = _truncate(context, MAX_CONTEXT_CHARS)
    messages = _build_messages(trimmed_answer, trimmed_context)

    try:
        raw = _call_ollama_judge(messages)
    except Exception as e:
        return {"skipped": True, "reason": f"API Error: {str(e)}"}

    parsed = _extract_json(raw)
    if not parsed:
        return {
            "skipped": True,
            "reason": "Judge response was not valid JSON",
            "raw_response": raw[:500],
        }

    return {
        "faithful": bool(parsed.get("faithful", False)),
        "score": float(parsed.get("score", 0.0)),
        "unsupported_claims": parsed.get("unsupported_claims", []) if isinstance(parsed.get("unsupported_claims"), list) else [],
        "notes": parsed.get("notes", ""),
    }


def evaluate_rag_faithfulness_llm(agent_outputs: dict, ground_truth: dict) -> dict:
    """
    Evaluate RAG faithfulness using a local Ollama LLM judge
    for the 3 specific targeted agents.
    """
    rag_gt = ground_truth.get("rag", {})
    rag_outputs = agent_outputs.get("rag", {})

    if not rag_gt:
        return {"skipped": True, "reason": "No RAG ground truth provided"}

    results: dict[str, Any] = {}
    evaluated = 0
    passed = 0
    skipped = 0

    for agent_name in rag_gt.keys():
        if agent_name not in TARGET_AGENTS:
            continue

        answer = agent_outputs.get(agent_name, "")
        context = rag_outputs.get(agent_name, {}).get("context", "")

        if not answer or not context:
            results[agent_name] = {"skipped": True, "reason": "Missing answer or retrieved context"}
            skipped += 1
            continue

        judge_result = _judge_faithfulness(answer, context)

        if judge_result.get("skipped"):
            results[agent_name] = judge_result
            skipped += 1
            continue

        evaluated += 1
        if judge_result.get("faithful") is True:
            passed += 1

        results[agent_name] = judge_result

    results["_summary"] = {
        "evaluated": evaluated,
        "passed": passed,
        "failed": evaluated - passed,
        "skipped": skipped,
        "pass_rate": round(passed / evaluated, 2) if evaluated > 0 else 0.0,
    }

    return results
