"""
RAG Faithfulness (LLM Judge)

Uses an LLM to verify that the agent answer is supported by the retrieved context.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from config import OLLAMA_BASE_URL, OLLAMA_MODEL


OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
JUDGE_MODEL = os.getenv("RAG_JUDGE_MODEL", OLLAMA_MODEL)
MAX_CONTEXT_CHARS = 6000
MAX_ANSWER_CHARS = 2000


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


def _extract_evidence_texts(parsed: dict | None) -> list[str]:
    if not parsed:
        return []

    evidence: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, val in node.items():
                if key == "evidence" and isinstance(val, str):
                    evidence.append(val)
                walk(val)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(parsed)
    return evidence


def _truncate_evidence_list(evidence: list[str]) -> str:
    if not evidence:
        return ""
    joined = "\n".join(f"- {item}" for item in evidence)
    return _truncate(joined, MAX_ANSWER_CHARS)


def _build_prompt(answer: str, context: str) -> str:
    return (
        "You are a strict fact-checker. Decide whether the ANSWER is fully supported by the CONTEXT.\n"
        "If any claim in the ANSWER is not explicitly supported by the CONTEXT, mark faithful=false.\n"
        "Do not assume missing information. Output JSON only with this schema:\n"
        '{"faithful": true/false, "score": 0-1, "unsupported_claims": ["..."], "notes": "..."}\n\n'
        "CONTEXT:\n"
        f"{context}\n\n"
        "ANSWER:\n"
        f"{answer}\n"
    )


def _call_ollama(prompt: str) -> str:
    payload = {
        "model": JUDGE_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 1.0,
        },
    }

    with httpx.Client(timeout=120.0) as client:
        response = client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")


def _judge_faithfulness(answer: str, context: str) -> dict[str, Any]:
    trimmed_answer = _truncate(answer, MAX_ANSWER_CHARS)
    trimmed_context = _truncate(context, MAX_CONTEXT_CHARS)

    prompt = _build_prompt(trimmed_answer, trimmed_context)
    raw = _call_ollama(prompt)
    parsed = _extract_json(raw)
    if not parsed:
        return {
            "skipped": True,
            "reason": "Judge response was not valid JSON",
            "raw_response": raw[:500],
        }

    faithful = bool(parsed.get("faithful", False))
    score = parsed.get("score", 0.0)
    unsupported = parsed.get("unsupported_claims", [])
    notes = parsed.get("notes", "")
    return {
        "faithful": faithful,
        "score": score,
        "unsupported_claims": unsupported if isinstance(unsupported, list) else [],
        "notes": notes,
    }


def evaluate_rag_faithfulness_llm(agent_outputs: dict, ground_truth: dict) -> dict:
    """
    Evaluate RAG faithfulness using an LLM judge.

    Requires RAG ground truth to identify which agents to evaluate:
    {
      "rag": { "risk": { ... }, "governance": { ... } }
    }
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
        raw_answer = agent_outputs.get(agent_name, "")
        parsed_answer = _extract_json(raw_answer)
        evidence_texts = _extract_evidence_texts(parsed_answer)
        answer = _truncate_evidence_list(evidence_texts)

        rag_meta = rag_outputs.get(agent_name, {}) or {}
        context_parts = [
            rag_meta.get("shared_context", ""),
            rag_meta.get("targeted_context", ""),
            rag_meta.get("context", ""),
        ]
        context = "\n\n---\n\n".join([part for part in context_parts if part])

        if not answer:
            results[agent_name] = {
                "skipped": True,
                "reason": "No evidence fields found in agent output",
            }
            skipped += 1
            continue

        if not context:
            results[agent_name] = {
                "skipped": True,
                "reason": "Missing retrieved context",
            }
            skipped += 1
            continue

        try:
            judge_result = _judge_faithfulness(answer, context)
        except Exception as e:
            results[agent_name] = {"skipped": True, "reason": f"Judge error: {str(e)}"}
            skipped += 1
            continue

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
        "pass_rate": round(passed / evaluated, 2) if evaluated > 0 else 0,
    }

    return results
