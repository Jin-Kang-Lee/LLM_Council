"""
EvalPipeline — Core evaluation orchestrator.

Loads test data, runs agents headlessly (no FastAPI), collects raw outputs,
and dispatches to evaluation functions.
"""

import json
import asyncio
import os
from datetime import datetime
from typing import Optional

from agents import RiskAgent, SentimentAgent, GovernanceAgent, DeepResearchAgent, MasterAgent
from document_parser import parse_earnings_content, format_for_agents
from config import MAX_DISCUSSION_ROUNDS
from eval.metrics.schema_integrity import evaluate_schema_integrity
from eval.metrics.reference_based import evaluate_reference_based
from eval.metrics.section_check import evaluate_section_completeness
from eval.metrics.query_diversity import evaluate_query_diversity


class EvalPipeline:
    """
    Orchestrates the full evaluation pipeline.

    Usage:
        pipeline = EvalPipeline(
            input_path="eval/test_data/test_data.json",
            tests=["schema", "reference"],
            output_dir="eval/results/"
        )
        asyncio.run(pipeline.run())
    """

    VALID_TESTS = ["schema", "reference", "section", "warroom", "diversity", "variance"]

    def __init__(
        self,
        input_path: str,
        tests: list[str],
        output_dir: str = "eval/results",
        openai_key: Optional[str] = None,
        variance_runs: int = 5,
        case_id: Optional[str] = None,
        verbose: bool = False,
    ):
        self.input_path = input_path
        self.tests = tests
        self.output_dir = output_dir
        self.openai_key = openai_key
        self.variance_runs = variance_runs
        self.case_id = case_id
        self.verbose = verbose

        # Loaded at runtime
        self.test_data: list[dict] = []
        self.results: dict = {}

    # ------------------------------------------------------------------ #
    #  Public entry point
    # ------------------------------------------------------------------ #
    async def run(self):
        """Main entry point — runs the full evaluation pipeline."""
        print("=" * 60)
        print("  LLM COUNCIL — EVALUATION PIPELINE")
        print("=" * 60)

        # 1. Load test data
        self._load_test_data()

        # 2. Initialise results container
        run_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.results = {
            "run_timestamp": run_timestamp,
            "tests_requested": self.tests,
            "test_cases": [],
        }

        # 3. Run each test case through the pipeline
        for test_case in self.test_data:
            # Skip if user filtered to a specific case
            if self.case_id and test_case["test_id"] != self.case_id:
                continue

            print(f"\n{'─' * 60}")
            print(f"  Test Case: {test_case['test_id']} — {test_case['description']}")
            print(f"{'─' * 60}")

            case_result = await self._run_single_case(test_case)
            self.results["test_cases"].append(case_result)

        # 4. Run evaluation metrics
        print(f"\n{'─' * 60}")
        print("  RUNNING EVALUATIONS")
        print(f"{'─' * 60}")
        self._run_evaluations()

        # 5. Save results
        self._save_results(run_timestamp)

        print(f"\n{'=' * 60}")
        print("  PIPELINE COMPLETE")
        print(f"{'=' * 60}")

    # ------------------------------------------------------------------ #
    #  Data loading
    # ------------------------------------------------------------------ #
    def _load_test_data(self):
        """Load and validate the test data JSON file."""
        print(f"\n📂 Loading test data from: {self.input_path}")

        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Test data file not found: {self.input_path}")

        with open(self.input_path, "r", encoding="utf-8") as f:
            self.test_data = json.load(f)

        count = len(self.test_data)
        ids = [tc["test_id"] for tc in self.test_data]
        print(f"   ✅ Loaded {count} test case(s): {', '.join(ids)}")

        # Validate case_id filter if provided
        if self.case_id and self.case_id not in ids:
            raise ValueError(
                f"Case ID '{self.case_id}' not found. Available: {', '.join(ids)}"
            )

    # ------------------------------------------------------------------ #
    #  Single test-case execution (runs all agents)
    # ------------------------------------------------------------------ #
    async def _run_single_case(self, test_case: dict) -> dict:
        """Run the full agent pipeline on a single test case."""
        test_id = test_case["test_id"]
        report_text = test_case["earnings_report"]

        # ── Phase 1: Parse the earnings report ──
        print(f"\n  [Phase 1] Parsing earnings report...")
        parsed = await parse_earnings_content(report_text)
        formatted = format_for_agents(parsed)
        print(f"   ✅ Parsed — {parsed['word_count']} words, topics: {parsed['sections_identified']}")

        # ── Phase 2: Individual agent analyses ──
        print(f"\n  [Phase 2] Running individual agent analyses...")

        risk_agent = RiskAgent()
        sentiment_agent = SentimentAgent()
        governance_agent = GovernanceAgent()
        research_agent = DeepResearchAgent()
        master_agent = MasterAgent()

        # Risk
        print(f"   🔴 Risk Agent analyzing...")
        risk_output = await risk_agent.analyze(formatted)
        print(f"   ✅ Risk Agent complete")
        if self.verbose:
            print(f"      Output preview: {risk_output[:200]}...")

        # Sentiment
        print(f"   🟢 Sentiment Agent analyzing...")
        sentiment_output = await sentiment_agent.analyze(formatted)
        print(f"   ✅ Sentiment Agent complete")
        if self.verbose:
            print(f"      Output preview: {sentiment_output[:200]}...")

        # Governance
        print(f"   🟣 Governance Agent analyzing...")
        governance_output = await governance_agent.analyze(formatted)
        print(f"   ✅ Governance Agent complete")
        if self.verbose:
            print(f"      Output preview: {governance_output[:200]}...")

        # Deep Research
        print(f"   🔵 Deep Research Agent analyzing...")
        research_output = await research_agent.analyze(formatted)
        print(f"   ✅ Deep Research Agent complete")
        if self.verbose:
            print(f"      Output preview: {research_output[:200]}...")

        # ── Phase 3: War Room Discussion ──
        print(f"\n  [Phase 3] Running War Room discussion ({MAX_DISCUSSION_ROUNDS} rounds)...")
        discussion_messages = []

        for round_num in range(1, MAX_DISCUSSION_ROUNDS + 1):
            print(f"   💬 Round {round_num}/{MAX_DISCUSSION_ROUNDS}...")

            # Risk responds
            if round_num == 1:
                prompt = risk_agent.respond_to("Sentiment Analyst", sentiment_output, formatted)
            else:
                last_msg = discussion_messages[-1]["content"]
                prompt = risk_agent.respond_to("Governance Analyst", last_msg, formatted)

            risk_response = await risk_agent.generate(formatted, prompt)
            discussion_messages.append({
                "agent": "Risk Analyst",
                "content": risk_response,
                "round": round_num,
            })

            # Sentiment responds to Risk
            prompt = sentiment_agent.respond_to("Risk Analyst", risk_response, formatted)
            sentiment_response = await sentiment_agent.generate(formatted, prompt)
            discussion_messages.append({
                "agent": "Sentiment Analyst",
                "content": sentiment_response,
                "round": round_num,
            })

            # Governance responds to both
            prompt = governance_agent.respond_to(
                "Risk and Sentiment Analysts",
                f"Risk says: {risk_response}\n\nSentiment says: {sentiment_response}",
                formatted,
            )
            gov_response = await governance_agent.generate(formatted, prompt)
            discussion_messages.append({
                "agent": "Governance Analyst",
                "content": gov_response,
                "round": round_num,
            })

        print(f"   ✅ War Room complete — {len(discussion_messages)} messages")

        # ── Phase 4: Master Agent Consolidation ──
        print(f"\n  [Phase 4] Master Agent consolidating...")
        discussion_transcript = "\n\n".join([
            f"**{msg['agent']} (Round {msg['round']}):**\n{msg['content']}"
            for msg in discussion_messages
        ])

        master_output = await master_agent.consolidate(
            formatted,
            risk_output,
            sentiment_output,
            governance_output,
            research_output,
            discussion_transcript,
        )
        print(f"   ✅ Final report generated")
        if self.verbose:
            print(f"      Output preview: {master_output[:300]}...")

        # ── Package results ──
        return {
            "test_id": test_id,
            "description": test_case["description"],
            "ground_truth": test_case["ground_truth"],
            "agent_outputs": {
                "risk": risk_output,
                "sentiment": sentiment_output,
                "governance": governance_output,
                "research": research_output,
                "discussion": discussion_messages,
                "master": master_output,
            },
        }

    # ------------------------------------------------------------------ #
    #  Evaluation dispatch
    # ------------------------------------------------------------------ #
    def _run_evaluations(self):
        """Dispatch collected outputs to the requested evaluation functions."""
        eval_results = {}

        for case in self.results["test_cases"]:
            test_id = case["test_id"]
            outputs = case["agent_outputs"]
            ground_truth = case["ground_truth"]
            print(f"\n  Evaluating {test_id}...")

            case_evals = {}

            if "schema" in self.tests or "all" in self.tests:
                print(f"   📋 Schema Integrity... ", end="")
                case_evals["schema_integrity"] = self._eval_schema_integrity(outputs)
                summary = case_evals["schema_integrity"].get("_summary", {})
                print(f"✅ {summary.get('passed', 0)}/{summary.get('total_agents', 0)} agents passed")

            if "reference" in self.tests or "all" in self.tests:
                print(f"   📊 Reference-Based Metrics... ", end="")
                case_evals["reference_based"] = self._eval_reference_based(outputs, ground_truth)
                summary = case_evals["reference_based"].get("_summary", {})
                print(f"✅ {summary.get('passed', 0)}/{summary.get('total_checks', 0)} checks passed")

            if "section" in self.tests or "all" in self.tests:
                print(f"   📝 Section Completeness... ", end="")
                case_evals["section_completeness"] = self._eval_section_completeness(outputs, ground_truth)
                sc = case_evals["section_completeness"]
                print(f"✅ {sc.get('completeness_rate', 0)*100:.0f}% sections found")

            if "warroom" in self.tests or "all" in self.tests:
                print(f"   🗣️  War Room (LLM-as-Judge)... ", end="")
                case_evals["warroom"] = self._eval_warroom(outputs)
                print("TODO")

            if "diversity" in self.tests or "all" in self.tests:
                print(f"   🔍 Query Diversity... ", end="")
                case_evals["query_diversity"] = self._eval_query_diversity(outputs)
                qd = case_evals["query_diversity"]
                print(f"✅ Diversity score: {qd.get('diversity_score', 'N/A')}")

            if "variance" in self.tests or "all" in self.tests:
                print(f"   🎲 Variance... ", end="")
                case_evals["variance"] = self._eval_variance(outputs)
                print("TODO")

            case["evaluations"] = case_evals

    # ------------------------------------------------------------------ #
    #  Evaluation stubs (to be implemented in Steps 3–6)
    # ------------------------------------------------------------------ #
    def _eval_schema_integrity(self, outputs: dict) -> dict:
        """Test 1: Check if agent outputs are valid JSON with correct schema."""
        return evaluate_schema_integrity(outputs)

    def _eval_reference_based(self, outputs: dict, ground_truth: dict) -> dict:
        """Test 2: Compare agent outputs against ground truth."""
        return evaluate_reference_based(outputs, ground_truth)

    def _eval_section_completeness(self, outputs: dict, ground_truth: dict) -> dict:
        """Test 3: Check Master Agent report has all required sections."""
        return evaluate_section_completeness(outputs, ground_truth)

    def _eval_warroom(self, outputs: dict) -> dict:
        """Test 4: LLM-as-a-Judge evaluation of War Room discussion."""
        # TODO: Implement in eval/metrics/llm_judge.py
        return {"status": "not_implemented"}

    def _eval_query_diversity(self, outputs: dict) -> dict:
        """Test 5: Evaluate diversity of Deep Research queries."""
        return evaluate_query_diversity(outputs)

    def _eval_variance(self, outputs: dict) -> dict:
        """Test 6: Variance across multiple runs (optional)."""
        # TODO: Implement in eval/metrics/variance.py
        return {"status": "not_implemented"}

    # ------------------------------------------------------------------ #
    #  Results output
    # ------------------------------------------------------------------ #
    def _save_results(self, run_timestamp: str):
        """Save evaluation results to a JSON file."""
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, f"eval_{run_timestamp}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Results saved to: {output_path}")
