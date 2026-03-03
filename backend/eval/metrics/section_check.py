"""
Section Completeness Test

Checks whether the Master Agent's final markdown report
contains all the required sections defined in the ground truth.
"""


def evaluate_section_completeness(agent_outputs: dict, ground_truth: dict) -> dict:
    """
    Check if the Master Agent's report contains all expected sections.

    Args:
        agent_outputs: dict containing 'master' key with the report text
        ground_truth: dict containing 'master.expected_sections' list

    Returns:
        Dict with per-section results and overall completeness rate.
    """
    master_output = agent_outputs.get("master", "")
    master_gt = ground_truth.get("master", {})
    expected_sections = master_gt.get("expected_sections", [])

    if not master_output:
        return {
            "skipped": True,
            "reason": "No master agent output found",
        }

    if not expected_sections:
        return {
            "skipped": True,
            "reason": "No expected sections defined in ground truth",
        }

    output_lower = master_output.lower()
    found = []
    missing = []

    for section in expected_sections:
        if section.lower() in output_lower:
            found.append(section)
        else:
            missing.append(section)

    total = len(expected_sections)
    completeness = round(len(found) / total, 2) if total > 0 else 0

    # Also check categorical fields if provided
    categorical_checks = {}

    if "expected_risk_level" in master_gt:
        expected = master_gt["expected_risk_level"].lower()
        categorical_checks["risk_level_mentioned"] = expected in output_lower

    if "expected_outlook" in master_gt:
        expected = master_gt["expected_outlook"].lower()
        categorical_checks["outlook_mentioned"] = expected in output_lower

    return {
        "expected_sections": expected_sections,
        "found_sections": found,
        "missing_sections": missing,
        "completeness_rate": completeness,
        "all_present": len(missing) == 0,
        "categorical_checks": categorical_checks,
    }
