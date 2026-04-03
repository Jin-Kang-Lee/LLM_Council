"""
RAG Retrieval Metrics

Evaluates whether retrieved reference context contains expected sources/keywords.
"""

from __future__ import annotations

import json
import re


_LEGACY_SOURCE_PATTERN = re.compile(r"^\[(.+?)\]\s*$")
_CHUNK_PREFIX_PATTERN = re.compile(r"^\[C\d+\]\s*(.+)$")
_CITATION_PATTERN = re.compile(r"\[C\d+\]")


def _extract_sources(reference_context: str) -> list[str]:
    sources: list[str] = []
    if not reference_context:
        return sources

    for line in reference_context.splitlines():
        stripped = line.strip()
        if not stripped.startswith("["):
            continue

        match = _CHUNK_PREFIX_PATTERN.match(stripped)
        if match:
            label = match.group(1)
        else:
            legacy = _LEGACY_SOURCE_PATTERN.match(stripped)
            if not legacy:
                continue
            label = legacy.group(1)

        filename = label.split("|", 1)[0].strip()
        if filename:
            sources.append(filename)
    return sources


def _compile_keyword_pattern(keyword: str) -> re.Pattern:
    escaped = re.escape(keyword.strip())
    if not escaped:
        return re.compile(r"$^")
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def _count_keyword_hits(text: str, keywords: list[str]) -> dict:
    if not keywords:
        return {"total": 0, "hits": 0, "matched": []}

    haystack = text or ""
    matched = []
    for kw in keywords:
        if not kw or not kw.strip():
            continue
        pattern = _compile_keyword_pattern(kw)
        if pattern.search(haystack):
            matched.append(kw)
    return {
        "total": len(keywords),
        "hits": len(matched),
        "matched": matched,
    }


def _normalize_list(items: list[str]) -> list[str]:
    return [item.strip().lower() for item in items if item and item.strip()]


def _try_parse_json(raw_output: str) -> dict | None:
    if not raw_output:
        return None
    try:
        parsed = json.loads(raw_output)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _flatten_text_values(value: object) -> str:
    chunks: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for item in node.values():
                walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            chunks.append(node)

    walk(value)
    return " ".join(chunks)


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


def _merge_contexts(primary: str, shared: str, targeted: str) -> str:
    if primary:
        return primary
    parts = [shared, targeted]
    merged = "\n\n---\n\n".join([p for p in parts if p])
    return merged


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
        rag_meta = rag_outputs.get(agent_name, {})
        agent_context = rag_meta.get("context", "")
        agent_query = rag_meta.get("query", "")
        shared_context = rag_meta.get("shared_context", "")
        targeted_context = rag_meta.get("targeted_context", "")
        combined_context = _merge_contexts(agent_context, shared_context, targeted_context)

        agent_answer = agent_outputs.get(agent_name, "")
        parsed_answer = _try_parse_json(agent_answer)
        answer_text = _flatten_text_values(parsed_answer) if parsed_answer else agent_answer
        evidence_texts = _extract_evidence_texts(parsed_answer)

        expected_sources = expectations.get("expected_sources", [])
        expected_keywords = expectations.get("expected_keywords", [])
        expected_facts = expectations.get("expected_facts", [])
        required_points = expectations.get("required_points", [])

        if not expected_sources and not expected_keywords and not expected_facts and not required_points:
            results[agent_name] = {"skipped": True, "reason": "No expectations set"}
            continue

        sources = _extract_sources(combined_context)
        unique_sources = list(dict.fromkeys(sources))

        source_hits = [s for s in expected_sources if s in unique_sources]
        source_hit_rate = round(len(source_hits) / len(expected_sources), 2) if expected_sources else 1.0

        keyword_stats = _count_keyword_hits(combined_context, expected_keywords)
        keyword_hit_rate = (
            round(keyword_stats["hits"] / keyword_stats["total"], 2)
            if keyword_stats["total"] > 0
            else 1.0
        )

        # Grounding: facts should appear in both answer and context
        fact_in_answer = _count_keyword_hits(answer_text, expected_facts)
        fact_in_context = _count_keyword_hits(combined_context, expected_facts)
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
        required_stats = _count_keyword_hits(answer_text, required_points)
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

        citation_required = bool(combined_context)
        citation_total = 0
        citation_hits = 0
        missing_citations: list[str] = []

        if citation_required and evidence_texts:
            citation_total = len(evidence_texts)
            for ev in evidence_texts:
                if _CITATION_PATTERN.search(ev):
                    citation_hits += 1
                else:
                    missing_citations.append(ev[:160])

        citation_coverage = (
            round(citation_hits / citation_total, 2) if citation_total > 0 else 1.0
        )

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
            "citation_required": citation_required,
            "citation_coverage": citation_coverage,
            "missing_citations": missing_citations,
            "shared_context_used": bool(shared_context),
            "targeted_context_used": bool(targeted_context),
        }

        if shared_context:
            shared_sources = _extract_sources(shared_context)
            shared_unique = list(dict.fromkeys(shared_sources))
            shared_source_hits = [s for s in expected_sources if s in shared_unique]
            shared_source_hit_rate = (
                round(len(shared_source_hits) / len(expected_sources), 2)
                if expected_sources
                else 1.0
            )
            shared_keyword_stats = _count_keyword_hits(shared_context, expected_keywords)
            shared_keyword_hit_rate = (
                round(shared_keyword_stats["hits"] / shared_keyword_stats["total"], 2)
                if shared_keyword_stats["total"] > 0
                else 1.0
            )
            results[agent_name]["shared"] = {
                "retrieved_sources": shared_unique,
                "source_hits": shared_source_hits,
                "source_hit_rate": shared_source_hit_rate,
                "keyword_hits": shared_keyword_stats["matched"],
                "keyword_hit_rate": shared_keyword_hit_rate,
            }

        if targeted_context:
            targeted_sources = _extract_sources(targeted_context)
            targeted_unique = list(dict.fromkeys(targeted_sources))
            targeted_source_hits = [s for s in expected_sources if s in targeted_unique]
            targeted_source_hit_rate = (
                round(len(targeted_source_hits) / len(expected_sources), 2)
                if expected_sources
                else 1.0
            )
            targeted_keyword_stats = _count_keyword_hits(targeted_context, expected_keywords)
            targeted_keyword_hit_rate = (
                round(targeted_keyword_stats["hits"] / targeted_keyword_stats["total"], 2)
                if targeted_keyword_stats["total"] > 0
                else 1.0
            )
            results[agent_name]["targeted"] = {
                "retrieved_sources": targeted_unique,
                "source_hits": targeted_source_hits,
                "source_hit_rate": targeted_source_hit_rate,
                "keyword_hits": targeted_keyword_stats["matched"],
                "keyword_hit_rate": targeted_keyword_hit_rate,
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
        "citation_total": sum(
            1
            for agent_result in results.values()
            if isinstance(agent_result, dict)
            and agent_result.get("citation_required")
        ),
        "citation_passed": sum(
            1
            for agent_result in results.values()
            if isinstance(agent_result, dict)
            and agent_result.get("citation_required")
            and agent_result.get("citation_coverage", 1.0) >= 1.0
        ),
    }

    return results
