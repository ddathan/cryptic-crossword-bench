"""Run an Inspect AI evaluation and automatically save the results."""

import sys  # noqa: E402
from pathlib import Path

import click
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


def parse_model_arg(arg: str) -> tuple[str, str | int | float | bool]:
    """Parse a model argument string in key=value format.

    Attempts to parse the value as: bool, int, float, or string.
    """
    if "=" not in arg:
        raise ValueError(f"Invalid model arg format: {arg}. Expected key=value")

    key, value = arg.split("=", 1)

    # Try to parse as bool
    if value.lower() in ("true", "false"):
        return key, value.lower() == "true"

    # Try to parse as int
    try:
        return key, int(value)
    except ValueError:
        pass

    # Try to parse as float
    try:
        return key, float(value)
    except ValueError:
        pass

    # Return as string
    return key, value


def run_and_save_eval(
    models: list[str],
    task: str = "cryptic_crossword",
    limit: int | None = None,
    benchmark_file: str | None = None,
    force: bool = False,
    model_args: dict[str, str | int | float | bool] | None = None,
) -> None:
    """Run an evaluation and save the results.

    Args:
        models: List of model identifiers (e.g., ["anthropic/claude-sonnet-4-20250514"])
        task: Task name (default: "cryptic_crossword")
        limit: Optional limit on number of samples
        benchmark_file: Optional path to specific benchmark file
        force: If True, skip duplicate check and override prompt
        model_args: Optional dict of model arguments (e.g., thinking budget)
    """
    logger.info(f"Running evaluation: {task}")
    logger.info(f"Models: {', '.join(models)}")
    if model_args:
        logger.info(f"Model args: {model_args}")
    logger.info("=" * 70)

    # Prepare task kwargs
    task_kwargs = {}
    if benchmark_file:
        task_kwargs["benchmark_file"] = benchmark_file

    # Prepare eval kwargs
    eval_kwargs: dict[str, object] = {
        "model": models,
        "limit": limit,
    }
    if model_args:
        eval_kwargs["model_args"] = model_args

    # Run the evaluation with all models
    # Inspect AI supports passing a list of models and will run them in parallel
    try:
        logs = inspect_eval(
            cryptic_crossword(**task_kwargs),
            **eval_kwargs,  # type: ignore[arg-type]
        )
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

    # Get the logs
    if not logs:
        logger.error("No evaluation logs generated")
        sys.exit(1)

    logger.info("\n" + "=" * 70)
    logger.info("Evaluation complete!")
    logger.info(f"Generated {len(logs)} log(s)")
    logger.info("=" * 70)

    # Save results for each log
    logger.info("\nSaving results...")
    saved_paths = []

    for log in logs:
        log_path = log.location
        logger.info(f"\nProcessing log: {log_path}")

        try:
            results_path = save_eval_results(log_path, force=force)
            saved_paths.append(results_path)
        except Exception as e:
            logger.error(f"Failed to save results for {log_path}: {e}")
            sys.exit(1)

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("✓ All results saved successfully!")
    logger.info(f"  Saved {len(saved_paths)} result file(s):")
    for path in saved_paths:
        logger.info(f"    - {path}")
    logger.info("=" * 70)


@click.command()
@click.option(
    "--model",
    "-m",
    "models",
    multiple=True,
    required=True,
    help="Model identifier(s). Can be specified multiple times to run multiple models.",
)
@click.option(
    "--task",
    default="cryptic_crossword",
    help="Task name (default: cryptic_crossword)",
)
@click.option(
    "--limit",
    type=int,
    help="Limit number of samples (optional)",
)
@click.option(
    "--benchmark-file",
    type=click.Path(exists=True),
    help="Path to specific benchmark file (optional)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip duplicate check and override prompt",
)
@click.option(
    "--model-arg",
    "-a",
    "model_args_raw",
    multiple=True,
    help="Model argument in key=value format. Can be specified multiple times.",
)
def main(
    models: tuple[str, ...],
    task: str,
    limit: int | None,
    benchmark_file: str | None,
    force: bool,
    model_args_raw: tuple[str, ...],
) -> None:
    """Run evaluation and save results.

    Examples:

      # Run on all crosswords with Claude Sonnet
      python eval/run_and_save.py --model anthropic/claude-sonnet-4-20250514

      # Run multiple models simultaneously
      python eval/run_and_save.py -m anthropic/claude-sonnet-4-20250514 \\
        -m anthropic/claude-opus-4-20250514

      # Run on a specific benchmark file
      python eval/run_and_save.py -m anthropic/claude-opus-4-20250514 \\
        --benchmark-file data/benchmark/crossword-cryptic-20260109-80222.json

      # Run with limited samples for testing
      python eval/run_and_save.py -m mockllm/model --limit 10

      # Run with model arguments (e.g., thinking budget)
      python eval/run_and_save.py -m anthropic/claude-sonnet-4-20250514 \\
        --model-arg thinking_budget=10000
    """
    # Parse model args
    model_args: dict[str, str | int | float | bool] | None = None
    if model_args_raw:
        model_args = {}
        for arg in model_args_raw:
            key, value = parse_model_arg(arg)
            model_args[key] = value

    run_and_save_eval(
        models=list(models),
        task=task,
        limit=limit,
        benchmark_file=benchmark_file,
        force=force,
        model_args=model_args,
    )


if __name__ == "__main__":
    main()
