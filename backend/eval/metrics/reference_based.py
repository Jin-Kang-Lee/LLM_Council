"""
Reference-Based Metrics

Compares agent outputs against ground truth using:
  - Level A: Categorical Accuracy (exact match on labels)
  - Level B: Content Recall (keyword-based fuzzy match on findings)
"""

import json


def _safe_parse(raw: str) -> dict | None:
    """Attempt to parse raw output as JSON, return None on failure."""
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _check_categorical(actual_value: str, expected_value: str) -> dict:
    """Exact match comparison for categorical fields."""
    match = actual_value.strip().lower() == expected_value.strip().lower()
    return {
        "expected": expected_value,
        "actual": actual_value,
        "match": match,
    }


def _check_score_range(actual_value, expected_range: list) -> dict:
    """Check if a numeric score falls within an expected range."""
    if not isinstance(actual_value, (int, float)):
        return {
            "expected_range": expected_range,
            "actual": actual_value,
            "in_range": False,
            "error": f"Value is not numeric: {type(actual_value).__name__}",
        }
    low, high = expected_range
    in_range = low <= actual_value <= high
    return {
        "expected_range": expected_range,
        "actual": actual_value,
        "in_range": in_range,
    }


def _check_keyword_recall(actual_text: str, expected_items: list[dict]) -> dict:
    """
    For each expected ground truth item (with 'keywords' list),
    check if ANY of its keywords appear in the agent's output text.

    Returns recall stats: how many expected items were "found" in the output.
    """
    actual_lower = actual_text.lower()
    found = 0
    details = []

    for item in expected_items:
        keywords = item.get("keywords", [])
        label = item.get("factor") or item.get("signal") or item.get("issue", "unknown")
        # An item is "found" if at least one keyword appears in the output
        matched_keywords = [kw for kw in keywords if kw.lower() in actual_lower]
        is_found = len(matched_keywords) > 0

        if is_found:
            found += 1

        details.append({
            "item": label,
            "found": is_found,
            "matched_keywords": matched_keywords,
        })

    total = len(expected_items)
    return {
        "total_expected": total,
        "found": found,
        "missed": total - found,
        "recall": round(found / total, 2) if total > 0 else 1.0,
        "details": details,
    }


# ── Per-agent evaluation functions ──────────────────────────────────────── #

def _eval_risk(parsed: dict, ground_truth: dict) -> dict:
    """Evaluate Risk Agent output against ground truth."""
    result = {}

    # Categorical: overall_risk_rating
    if "overall_risk_rating" in parsed and "overall_risk_rating" in ground_truth:
        result["overall_risk_rating"] = _check_categorical(
            parsed["overall_risk_rating"], ground_truth["overall_risk_rating"]
        )

    # Score range: liquidity_score
    if "liquidity_score" in parsed and "liquidity_score_range" in ground_truth:
        result["liquidity_score"] = _check_score_range(
            parsed["liquidity_score"], ground_truth["liquidity_score_range"]
        )

    # Score range: confidence_score
    if "confidence_score" in parsed and "confidence_score_range" in ground_truth:
        result["confidence_score"] = _check_score_range(
            parsed["confidence_score"], ground_truth["confidence_score_range"]
        )

    # Content recall: key_risk_factors
    if "key_risk_factors" in ground_truth:
        # Use the full raw output text for keyword matching
        raw_text = json.dumps(parsed)
        result["key_risk_factors_recall"] = _check_keyword_recall(
            raw_text, ground_truth["key_risk_factors"]
        )

    return result


def _eval_business_ops(parsed: dict, ground_truth: dict) -> dict:
    """Evaluate Business & Ops Agent output against ground truth."""
    result = {}

    # Categorical: operational_risk_rating
    if "operational_risk_rating" in parsed and "operational_risk_rating" in ground_truth:
        result["operational_risk_rating"] = _check_categorical(
            parsed["operational_risk_rating"], ground_truth["operational_risk_rating"]
        )

    # Score range: confidence_score
    if "confidence_score" in parsed and "confidence_score_range" in ground_truth:
        result["confidence_score"] = _check_score_range(
            parsed["confidence_score"], ground_truth["confidence_score_range"]
        )

    # Content recall: key_business_risks
    if "key_business_risks" in ground_truth:
        raw_text = json.dumps(parsed)
        result["key_business_risks_recall"] = _check_keyword_recall(
            raw_text, ground_truth["key_business_risks"]
        )

    return result


def _eval_governance(parsed: dict, ground_truth: dict) -> dict:
    """Evaluate Governance Agent output against ground truth."""
    result = {}

    # Categorical matches
    for field in ["governance_risk_level", "compliance_risk_level"]:
        if field in parsed and field in ground_truth:
            result[field] = _check_categorical(parsed[field], ground_truth[field])

    # Score range: confidence_score
    if "confidence_score" in parsed and "confidence_score_range" in ground_truth:
        result["confidence_score"] = _check_score_range(
            parsed["confidence_score"], ground_truth["confidence_score_range"]
        )

    # Content recall: key_findings (only if ground truth has findings)
    if ground_truth.get("key_findings"):
        raw_text = json.dumps(parsed)
        result["key_findings_recall"] = _check_keyword_recall(
            raw_text, ground_truth["key_findings"]
        )

    return result


def _eval_research(parsed: dict, ground_truth: dict) -> dict:
    """Evaluate research output against ground truth."""
    result = {}

    # Check minimum query count
    queries = parsed.get("search_queries", [])
    min_count = ground_truth.get("min_query_count", 0)
    result["query_count"] = {
        "expected_min": min_count,
        "actual": len(queries),
        "met": len(queries) >= min_count,
    }

    # Check expected topics are covered
    expected_topics = ground_truth.get("expected_topics", [])
    if expected_topics:
        raw_text = json.dumps(parsed).lower()
        found_topics = [t for t in expected_topics if t.lower() in raw_text]
        result["topic_coverage"] = {
            "expected_topics": expected_topics,
            "found_topics": found_topics,
            "missed_topics": [t for t in expected_topics if t not in found_topics],
            "coverage": round(len(found_topics) / len(expected_topics), 2),
        }

    return result


# ── Public API ──────────────────────────────────────────────────────────── #

AGENT_EVALUATORS = {
    "risk": _eval_risk,
    "business_ops": _eval_business_ops,
    "governance": _eval_governance,
    "research": _eval_research,
}


def evaluate_reference_based(agent_outputs: dict, ground_truth: dict) -> dict:
    """
    Compare agent outputs against ground truth.

    Args:
        agent_outputs: dict with keys 'risk', 'sentiment', 'governance', 'research'
        ground_truth: dict with matching keys containing expected values

    Returns:
        Dict with per-agent comparison results and summary stats.
    """
    results = {}
    total_checks = 0
    passed_checks = 0

    for agent_name, evaluator in AGENT_EVALUATORS.items():
        raw = agent_outputs.get(agent_name, "")
        gt = ground_truth.get(agent_name, {})

        if not gt:
            results[agent_name] = {"skipped": True, "reason": "No ground truth provided"}
            continue

        parsed = _safe_parse(raw)
        if parsed is None:
            results[agent_name] = {
                "skipped": True,
                "reason": "Could not parse agent output as JSON",
            }
            continue

        agent_result = evaluator(parsed, gt)

        # Count pass/fail for categorical and range checks
        for key, val in agent_result.items():
            if isinstance(val, dict):
                if "match" in val:
                    total_checks += 1
                    if val["match"]:
                        passed_checks += 1
                if "in_range" in val:
                    total_checks += 1
                    if val["in_range"]:
                        passed_checks += 1
                if "met" in val:
                    total_checks += 1
                    if val["met"]:
                        passed_checks += 1

        results[agent_name] = agent_result

    results["_summary"] = {
        "total_checks": total_checks,
        "passed": passed_checks,
        "failed": total_checks - passed_checks,
        "accuracy": round(passed_checks / total_checks, 2) if total_checks > 0 else 0,
    }

    return results
