"""
CLI Entry Point for the LLM Council Evaluation Pipeline.

Usage:
    python start_test.py --input="eval/test_data/test_data.json" --tests=all
    python start_test.py --input="eval/test_data/test_data.json" --tests=schema,reference
    python start_test.py --input="eval/test_data/test_data.json" --tests=warroom --openai_key=sk-...
    python start_test.py --input="eval/test_data/test_data.json" --tests=variance --runs=5
    python start_test.py --input="eval/test_data/test_data.json" --tests=all --case=TC-001 --verbose
"""

import argparse
import asyncio
import sys

from eval.pipeline import EvalPipeline


def parse_args():
    """Parse and validate CLI arguments."""
    parser = argparse.ArgumentParser(
        description="LLM Council Evaluation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_test.py --input="eval/test_data/test_data.json" --tests=all
  python start_test.py --input="eval/test_data/test_data.json" --tests=schema,reference
  python start_test.py --input="eval/test_data/test_data.json" --tests=all --case=TC-001
  python start_test.py --input="eval/test_data/test_data.json" --tests=warroom --openai_key=sk-...
        """,
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the test data JSON file (e.g., eval/test_data/test_data.json)",
    )

    parser.add_argument(
        "--tests",
        type=str,
        required=True,
        help=(
            "Comma-separated list of tests to run. "
            "Options: schema, reference, section, warroom, diversity, variance, rag, rag_faithfulness, all"
        ),
    )

    parser.add_argument(
        "--output",
        type=str,
        default="eval/results",
        help="Output directory for results (default: eval/results/)",
    )

    parser.add_argument(
        "--openai_key",
        type=str,
        default=None,
        help="OpenAI API key (required for 'warroom' test)",
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of runs for variance test (default: 5)",
    )

    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Run only a specific test case by ID (e.g., TC-001)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed agent outputs during the run",
    )

    return parser.parse_args()


def validate_tests(tests_str: str) -> list[str]:
    """Validate and parse the --tests argument."""
    valid = {"schema", "reference", "section", "warroom", "diversity", "variance", "rag", "rag_faithfulness", "all"}
    tests = [t.strip().lower() for t in tests_str.split(",")]

    invalid = [t for t in tests if t not in valid]
    if invalid:
        print(f"❌ Invalid test name(s): {', '.join(invalid)}")
        print(f"   Valid options: {', '.join(sorted(valid))}")
        sys.exit(1)

    return tests


def main():
    args = parse_args()

    # Validate tests
    tests = validate_tests(args.tests)

    # Check for OpenAI key if warroom test is requested
    if ("warroom" in tests or "all" in tests) and not args.openai_key:
        print("⚠️  Warning: 'warroom' test requires --openai_key. It will be skipped.")

    # Create and run the pipeline
    pipeline = EvalPipeline(
        input_path=args.input,
        tests=tests,
        output_dir=args.output,
        openai_key=args.openai_key,
        variance_runs=args.runs,
        case_id=args.case,
        verbose=args.verbose,
    )

    # Run the async pipeline
    asyncio.run(pipeline.run())


if __name__ == "__main__":
    main()
