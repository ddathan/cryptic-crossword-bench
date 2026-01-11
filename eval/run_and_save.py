"""Run an Inspect AI evaluation and automatically save the results."""

import sys  # noqa: E402
from pathlib import Path

from dotenv import load_dotenv
from inspect_ai import eval as inspect_eval
from loguru import logger

# Add project root to path to enable imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eval.cryptic_crossword_eval import cryptic_crossword  # noqa: E402
from eval.save_results import save_eval_results  # noqa: E402

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")


def run_and_save_eval(
    model: str,
    task: str = "cryptic_crossword",
    limit: int | None = None,
    benchmark_file: str | None = None,
) -> None:
    """Run an evaluation and save the results.

    Args:
        model: Model identifier (e.g., "anthropic/claude-sonnet-4-20250514")
        task: Task name (default: "cryptic_crossword")
        limit: Optional limit on number of samples
        benchmark_file: Optional path to specific benchmark file
    """
    logger.info(f"Running evaluation: {task} with {model}")
    logger.info("=" * 70)

    # Prepare task kwargs
    task_kwargs = {}
    if benchmark_file:
        task_kwargs["benchmark_file"] = benchmark_file

    # Run the evaluation
    try:
        logs = inspect_eval(
            cryptic_crossword(**task_kwargs),
            model=model,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

    # Get the log
    if not logs:
        logger.error("No evaluation logs generated")
        sys.exit(1)

    log = logs[0]
    log_path = log.location

    logger.info("\n" + "=" * 70)
    logger.info("Evaluation complete!")
    logger.info(f"Log saved to: {log_path}")
    logger.info("=" * 70)

    # Save results
    logger.info("\nSaving results...")
    try:
        results_path = save_eval_results(log_path)
        logger.info(f"\n✓ Results saved successfully to: {results_path}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        sys.exit(1)


def main() -> None:
    """CLI entrypoint."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run evaluation and save results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run on all crosswords with Claude Sonnet
  python eval/run_and_save.py --model anthropic/claude-sonnet-4-20250514

  # Run on a specific benchmark file
  python eval/run_and_save.py --model anthropic/claude-opus-4-20250514 \\
    --benchmark-file data/benchmark/crossword-cryptic-20260109-80222.json

  # Run with limited samples for testing
  python eval/run_and_save.py --model mockllm/model --limit 10
        """,
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Model identifier (e.g., 'anthropic/claude-sonnet-4-20250514')",
    )
    parser.add_argument(
        "--task",
        default="cryptic_crossword",
        help="Task name (default: cryptic_crossword)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of samples (optional)",
    )
    parser.add_argument(
        "--benchmark-file",
        help="Path to specific benchmark file (optional)",
    )

    args = parser.parse_args()

    run_and_save_eval(
        model=args.model,
        task=args.task,
        limit=args.limit,
        benchmark_file=args.benchmark_file,
    )


if __name__ == "__main__":
    main()
