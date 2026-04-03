"""
War Room Capture Script
-----------------------
Runs the 3 specialist agents + War Room discussion
for each test case in test_data.json, then saves everything to
eval/warroom_captures/ for later LLM-as-Judge evaluation.

NO master agent. NO UI. Just raw agent outputs + the full discussion thread.

Usage:
    python -m eval.capture_warroom
    python -m eval.capture_warroom --case TC-001
    python -m eval.capture_warroom --input path/to/custom_data.json
"""

import asyncio
import json
import os
import argparse
from datetime import datetime

from agents import RiskAgent, BusinessOpsRiskAgent, GovernanceAgent
from document_parser import parse_earnings_content, format_for_agents
from config import MAX_DISCUSSION_ROUNDS
from rag.retriever import build_shared_reference_query, get_council_context, ensure_ingested

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT = os.path.join(CURRENT_DIR, "test_data", "test_data.json")
DEFAULT_OUTPUT_DIR = os.path.join(CURRENT_DIR, "warroom_captures")


async def run_case(test_case: dict) -> dict:
    test_id = test_case["test_id"]
    description = test_case["description"]
    report_text = test_case["earnings_report"]

    print(f"\n{'-' * 60}")
    print(f"  {test_id} — {description}")
    print(f"{'-' * 60}")

    # ── Phase 1: Parse ──
    print("  [1] Parsing report...")
    parsed = await parse_earnings_content(report_text)
    formatted = format_for_agents(parsed)
    shared_query = build_shared_reference_query(formatted)
    shared_context = get_council_context(shared_query) if shared_query else ""
    print(f"      {parsed['word_count']} words, sections: {parsed['sections_identified']}")

    # ── Phase 2: Individual analyses ──
    print("  [2] Running specialist agents...")
    risk_agent = RiskAgent()
    business_ops_agent = BusinessOpsRiskAgent()
    governance_agent = GovernanceAgent()

    kwargs = dict(
        reference_context=shared_context,
        reference_query=shared_query,
        allow_targeted_retrieval=True,
    )

    print("      Risk Agent...")
    risk_output = await risk_agent.analyze(formatted, **kwargs)

    print("      Business & Ops Agent...")
    business_ops_output = await business_ops_agent.analyze(formatted, **kwargs)

    print("      Governance Agent...")
    governance_output = await governance_agent.analyze(formatted, **kwargs)


    # ── Phase 2.5: Position papers ──
    print("  [2.5] Generating position papers...")
    risk_position, business_ops_position, governance_position = await asyncio.gather(
        risk_agent.write_position_paper(risk_output),
        business_ops_agent.write_position_paper(business_ops_output),
        governance_agent.write_position_paper(governance_output),
    )
    position_papers = {
        "Risk Analyst": risk_position,
        "Business & Ops Analyst": business_ops_position,
        "Governance Analyst": governance_position,
    }

    # ── Phase 3: War Room ──
    print(f"  [3] War Room ({MAX_DISCUSSION_ROUNDS} rounds)...")
    discussion_messages = []

    for round_num in range(1, MAX_DISCUSSION_ROUNDS + 1):
        print(f"      Round {round_num}/{MAX_DISCUSSION_ROUNDS}...")

        # Risk opens round 1; subsequent rounds challenge Governance's last point
        if round_num == 1:
            risk_turn = (
                "The war room is open. You go first — pick the sharpest disagreement "
                "between the three positions and make your opening move. "
                "Lead with a specific number or metric from the report."
            )
        else:
            gov_msg = next((m for m in reversed(discussion_messages) if m["agent"] == "Governance Analyst"), None)
            risk_turn = risk_agent.respond_to(
                "Governance Analyst",
                gov_msg["content"] if gov_msg else discussion_messages[-1]["content"]
            )

        risk_response = await risk_agent.generate_discussion(
            position_papers, discussion_messages, risk_turn,
            earnings_content=formatted
        )
        discussion_messages.append({"agent": "Risk Analyst", "content": risk_response, "round": round_num})

        business_ops_response = await business_ops_agent.generate_discussion(
            position_papers,
            discussion_messages,
            business_ops_agent.respond_to("Risk Analyst", risk_response),
            earnings_content=formatted
        )
        discussion_messages.append({"agent": "Business & Ops Analyst", "content": business_ops_response, "round": round_num})

        if round_num == 1:
            gov_turn = (
                "Risk and Business & Ops have both weighed in. "
                "What are they missing or getting wrong from a governance and compliance standpoint? "
                "Be specific — name the exact claim you are pushing back on."
            )
        else:
            gov_turn = (
                f"Risk just argued: '{risk_response[:400]}...'\n"
                f"Business & Ops countered: '{business_ops_response[:400]}...'\n\n"
                "Pick the argument you find most legally or regulatory problematic and challenge it. "
                "Cite a specific compliance requirement or governance gap they are ignoring."
            )

        gov_response = await governance_agent.generate_discussion(
            position_papers, discussion_messages, gov_turn,
            earnings_content=formatted
        )
        discussion_messages.append({"agent": "Governance Analyst", "content": gov_response, "round": round_num})

    print(f"      War Room complete — {len(discussion_messages)} messages")

    return {
        "test_id": test_id,
        "description": description,
        "captured_at": datetime.now().isoformat(),
        "report_word_count": parsed["word_count"],
        "agent_outputs": {
            "risk": risk_output,
            "business_ops": business_ops_output,
            "governance": governance_output,
        },
        "position_papers": position_papers,
        "discussion": discussion_messages,
    }


async def main(input_path: str, output_dir: str, case_id: str | None):
    print("=" * 60)
    print("  WAR ROOM CAPTURE")
    print("=" * 60)

    ensure_ingested()

    with open(input_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    for test_case in test_data:
        if case_id and test_case["test_id"] != case_id:
            continue

        capture = await run_case(test_case)

        # Save one file per test case
        filename = f"{capture['test_id']}_{timestamp}.json"
        out_path = os.path.join(output_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(capture, f, indent=2, ensure_ascii=False)
        print(f"\n  Saved: {out_path}")

    print(f"\n{'=' * 60}")
    print("  CAPTURE COMPLETE")
    print(f"  Output dir: {output_dir}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture war room discussions for LLM-as-Judge eval")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to test data JSON")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--case", default=None, help="Run only a specific test case ID (e.g. TC-001)")
    args = parser.parse_args()

    asyncio.run(main(args.input, args.output, args.case))
