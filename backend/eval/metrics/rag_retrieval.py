"""
RAG Retrieval Metrics

Evaluates whether retrieved reference context contains expected sources/keywords.
"""

from __future__ import annotations

import re


_SOURCE_PATTERN = re.compile(r"^\[(.+?)\]\s*$")


def _extract_sources(reference_context: str) -> list[str]:
    sources: list[str] = []
    if not reference_context:
        return sources

    for line in reference_context.splitlines():
        match = _SOURCE_PATTERN.match(line.strip())
        if match:
            sources.append(match.group(1))
    return sources


def _count_keyword_hits(text: str, keywords: list[str]) -> dict:
    if not keywords:
        return {"total": 0, "hits": 0, "matched": []}

    haystack = (text or "").lower()
    matched = [kw for kw in keywords if kw.lower() in haystack]
    return {
        "total": len(keywords),
        "hits": len(matched),
        "matched": matched,
    }


def _normalize_list(items: list[str]) -> list[str]:
    return [item.strip().lower() for item in items if item and item.strip()]


def evaluate_rag_retrieval(agent_outputs: dict, ground_truth: dict) -> dict:
    """
    Evaluate RAG retrieval quality using expected sources/keywords.

    Expected ground truth format:
    {
      "rag": {
        "risk": {
          "expected_sources": ["PWC_ASC606.md"],
          "expected_keywords": ["variable consideration"],
          "expected_facts": ["variable consideration"],
          "required_points": ["ASC 606"]
        },
        "sentiment": { ... },
        "governance": { ... },
        "research": { ... }
      }
    }
    """
    rag_gt = ground_truth.get("rag", {})
    rag_outputs = agent_outputs.get("rag", {})

    if not rag_gt:
        return {"skipped": True, "reason": "No RAG ground truth provided"}

    results: dict = {}
    total_checks = 0
    passed_checks = 0
    grounding_total = 0
    grounding_passed = 0
    answer_total = 0
    answer_passed = 0

    for agent_name, expectations in rag_gt.items():
        agent_context = rag_outputs.get(agent_name, {}).get("context", "")
        agent_query = rag_outputs.get(agent_name, {}).get("query", "")
        agent_answer = agent_outputs.get(agent_name, "")

        expected_sources = expectations.get("expected_sources", [])
        expected_keywords = expectations.get("expected_keywords", [])
        expected_facts = expectations.get("expected_facts", [])
        required_points = expectations.get("required_points", [])

        if not expected_sources and not expected_keywords and not expected_facts and not required_points:
            results[agent_name] = {"skipped": True, "reason": "No expectations set"}
            continue

        sources = _extract_sources(agent_context)
        unique_sources = list(dict.fromkeys(sources))

        source_hits = [s for s in expected_sources if s in unique_sources]
        source_hit_rate = round(len(source_hits) / len(expected_sources), 2) if expected_sources else 1.0

        keyword_stats = _count_keyword_hits(agent_context, expected_keywords)
        keyword_hit_rate = (
            round(keyword_stats["hits"] / keyword_stats["total"], 2)
            if keyword_stats["total"] > 0
            else 1.0
        )

        # Grounding: facts should appear in both answer and context
        fact_in_answer = _count_keyword_hits(agent_answer, expected_facts)
        fact_in_context = _count_keyword_hits(agent_context, expected_facts)
        answer_facts_set = set(_normalize_list(fact_in_answer["matched"]))
        context_facts_set = set(_normalize_list(fact_in_context["matched"]))
        supported_facts = [
            fact
            for fact in expected_facts
            if fact.strip().lower() in answer_facts_set
            and fact.strip().lower() in context_facts_set
        ]
        grounding_rate = (
            round(len(supported_facts) / len(expected_facts), 2)
            if expected_facts
            else 1.0
        )

        # Answer quality: required points should appear in answer
        required_stats = _count_keyword_hits(agent_answer, required_points)
        required_coverage_rate = (
            round(required_stats["hits"] / required_stats["total"], 2)
            if required_stats["total"] > 0
            else 1.0
        )

        total_checks += 1
        if expected_sources:
            if source_hit_rate >= 0.5:
                passed_checks += 1
        else:
            if keyword_hit_rate >= 0.5:
                passed_checks += 1

        if expected_facts:
            grounding_total += 1
            if grounding_rate >= 0.5:
                grounding_passed += 1

        if required_points:
            answer_total += 1
            if required_coverage_rate >= 0.5:
                answer_passed += 1

        results[agent_name] = {
            "query": agent_query,
            "retrieved_sources": unique_sources,
            "expected_sources": expected_sources,
            "source_hits": source_hits,
            "source_hit_rate": source_hit_rate,
            "expected_keywords": expected_keywords,
            "keyword_hits": keyword_stats["matched"],
            "keyword_hit_rate": keyword_hit_rate,
            "expected_facts": expected_facts,
            "answer_facts": fact_in_answer["matched"],
            "context_facts": fact_in_context["matched"],
            "supported_facts": supported_facts,
            "grounding_rate": grounding_rate,
            "required_points": required_points,
            "required_points_found": required_stats["matched"],
            "required_coverage_rate": required_coverage_rate,
        }

    results["_summary"] = {
        "total_checks": total_checks,
        "passed": passed_checks,
        "failed": total_checks - passed_checks,
        "pass_rate": round(passed_checks / total_checks, 2) if total_checks > 0 else 0,
        "grounding_total": grounding_total,
        "grounding_passed": grounding_passed,
        "grounding_failed": grounding_total - grounding_passed,
        "grounding_pass_rate": round(grounding_passed / grounding_total, 2)
        if grounding_total > 0
        else 0,
        "answer_total": answer_total,
        "answer_passed": answer_passed,
        "answer_failed": answer_total - answer_passed,
        "answer_pass_rate": round(answer_passed / answer_total, 2)
        if answer_total > 0
        else 0,
    }

    return results
