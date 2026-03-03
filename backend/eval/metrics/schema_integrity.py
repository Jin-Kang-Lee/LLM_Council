"""
Schema Integrity Test

Checks whether agent outputs are valid JSON and conform to
the expected schema (required keys, correct types, valid enum values).
"""

import json


# ── Expected schemas per agent ──────────────────────────────────────────── #

RISK_SCHEMA = {
    "required_keys": {
        "overall_risk_rating": {"type": str, "enum": ["Low", "Medium", "High", "Critical"]},
        "liquidity_score": {"type": (int, float)},
        "key_risk_factors": {"type": list},
        "watchlist": {"type": list},
        "confidence_score": {"type": (int, float)},
    },
    "nested": {
        "key_risk_factors": {
            "required_keys": {
                "factor": {"type": str},
                "impact": {"type": str},
                "severity": {"type": str, "enum": ["Low", "Medium", "High", "Critical"]},
                "evidence": {"type": str},
            }
        }
    },
}

SENTIMENT_SCHEMA = {
    "required_keys": {
        "overall_sentiment_score": {
            "type": str,
            "enum": ["Very Negative", "Negative", "Neutral", "Positive", "Very Positive"],
        },
        "executive_confidence": {"type": str, "enum": ["Low", "Moderate", "High"]},
        "forward_outlook": {"type": str, "enum": ["Bearish", "Neutral", "Bullish"]},
        "key_signals": {"type": list},
        "language_patterns": {"type": list},
        "transparency_score": {"type": (int, float)},
    },
    "nested": {
        "key_signals": {
            "required_keys": {
                "signal": {"type": str},
                "sentiment": {"type": str, "enum": ["Positive", "Negative", "Neutral"]},
                "evidence": {"type": str},
                "explanation": {"type": str},
            }
        }
    },
}

GOVERNANCE_SCHEMA = {
    "required_keys": {
        "governance_risk_level": {"type": str, "enum": ["Low", "Medium", "High"]},
        "compliance_risk_level": {"type": str, "enum": ["Low", "Medium", "High"]},
        "key_findings": {"type": list},
        "non_disclosures": {"type": list},
        "confidence_score": {"type": (int, float)},
        "limitations": {"type": str},
    },
    "nested": {
        "key_findings": {
            "required_keys": {
                "issue": {"type": str},
                "category": {"type": str, "enum": ["Governance", "Legal", "Compliance", "Accounting"]},
                "severity": {"type": str, "enum": ["Low", "Medium", "High"]},
                "evidence": {"type": str},
                "impact": {"type": str},
            }
        }
    },
}

RESEARCH_SCHEMA = {
    "required_keys": {
        "thinking_trace": {"type": str},
        "search_queries": {"type": list},
        "confidence_gap": {"type": str},
    },
    "nested": {
        "search_queries": {
            "required_keys": {
                "topic": {"type": str},
                "query": {"type": str},
                "rationale": {"type": str},
                "status": {"type": str},
                "result": {"type": (str, type(None))},
            }
        }
    },
}

AGENT_SCHEMAS = {
    "risk": RISK_SCHEMA,
    "sentiment": SENTIMENT_SCHEMA,
    "governance": GOVERNANCE_SCHEMA,
    "research": RESEARCH_SCHEMA,
}


# ── Core validation logic ───────────────────────────────────────────────── #

def _validate_json_parse(raw_output: str) -> tuple[bool, dict | None, str]:
    """Try to parse raw output as JSON. Returns (success, parsed_dict, error_msg)."""
    try:
        parsed = json.loads(raw_output)
        if not isinstance(parsed, dict):
            return False, None, f"Parsed JSON is {type(parsed).__name__}, expected dict"
        return True, parsed, ""
    except json.JSONDecodeError as e:
        return False, None, f"JSON parse error: {e}"


def _validate_schema(parsed: dict, schema: dict) -> list[str]:
    """
    Validate a parsed dict against a schema definition.
    Returns a list of error strings (empty if fully compliant).
    """
    errors = []
    required = schema.get("required_keys", {})
    nested = schema.get("nested", {})

    # Check required top-level keys
    for key, rules in required.items():
        if key not in parsed:
            errors.append(f"Missing required key: '{key}'")
            continue

        value = parsed[key]

        # Type check (allow None for nullable fields)
        expected_type = rules.get("type")
        if expected_type and not isinstance(value, expected_type):
            errors.append(
                f"Key '{key}': expected type {expected_type}, got {type(value).__name__}"
            )
            continue

        # Enum check
        allowed = rules.get("enum")
        if allowed and isinstance(value, str) and value not in allowed:
            errors.append(
                f"Key '{key}': value '{value}' not in allowed values {allowed}"
            )

    # Check nested array items
    for key, nested_schema in nested.items():
        if key not in parsed or not isinstance(parsed[key], list):
            continue
        for i, item in enumerate(parsed[key]):
            if not isinstance(item, dict):
                errors.append(f"'{key}[{i}]': expected dict, got {type(item).__name__}")
                continue
            for nested_key, nested_rules in nested_schema["required_keys"].items():
                if nested_key not in item:
                    errors.append(f"'{key}[{i}]': missing required key '{nested_key}'")
                    continue
                nested_val = item[nested_key]
                expected_type = nested_rules.get("type")
                if expected_type and not isinstance(nested_val, expected_type):
                    errors.append(
                        f"'{key}[{i}].{nested_key}': expected {expected_type}, "
                        f"got {type(nested_val).__name__}"
                    )
                    continue
                allowed = nested_rules.get("enum")
                if allowed and isinstance(nested_val, str) and nested_val not in allowed:
                    errors.append(
                        f"'{key}[{i}].{nested_key}': value '{nested_val}' "
                        f"not in {allowed}"
                    )

    return errors


# ── Public API ──────────────────────────────────────────────────────────── #

def evaluate_schema_integrity(agent_outputs: dict) -> dict:
    """
    Run schema integrity checks on all JSON-producing agents.

    Args:
        agent_outputs: dict with keys 'risk', 'sentiment', 'governance', 'research'

    Returns:
        Dict with per-agent results and an overall pass rate.
    """
    results = {}
    total = 0
    passed = 0

    for agent_name, schema in AGENT_SCHEMAS.items():
        total += 1
        raw = agent_outputs.get(agent_name, "")

        # Step 1: Can we parse it as JSON?
        json_ok, parsed, parse_error = _validate_json_parse(raw)

        if not json_ok:
            results[agent_name] = {
                "json_valid": False,
                "json_error": parse_error,
                "schema_valid": False,
                "schema_errors": [],
                "passed": False,
            }
            continue

        # Step 2: Does it match the expected schema?
        schema_errors = _validate_schema(parsed, schema)
        is_valid = len(schema_errors) == 0

        if is_valid:
            passed += 1

        results[agent_name] = {
            "json_valid": True,
            "json_error": "",
            "schema_valid": is_valid,
            "schema_errors": schema_errors,
            "passed": is_valid,
        }

    results["_summary"] = {
        "total_agents": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 2) if total > 0 else 0,
    }

    return results
