"""Save Inspect AI evaluation results to the results directory."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from inspect_ai.log import EvalLog, read_eval_log
from loguru import logger

# API pricing per 1M tokens (USD)
# Format: {model_pattern: {"input": price, "output": price}}
# Patterns are matched from start of model name
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Anthropic models
    "anthropic/claude-opus-4": {"input": 15.0, "output": 75.0},
    "anthropic/claude-sonnet-4": {"input": 3.0, "output": 15.0},
    "anthropic/claude-haiku-4": {"input": 0.80, "output": 4.0},
    "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
    "anthropic/claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
    # OpenAI models
    "openai/gpt-5": {"input": 2.0, "output": 8.0},
    "openai/gpt-4o": {"input": 2.50, "output": 10.0},
    "openai/gpt-4.1": {"input": 2.0, "output": 8.0},
    "openai/o3": {"input": 2.0, "output": 8.0},
    "openai/o1": {"input": 15.0, "output": 60.0},
    # Google models
    "google/gemini-3": {"input": 1.25, "output": 10.0},
    "google/gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    "google/gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "google/gemini-2.0": {"input": 0.10, "output": 0.40},
    "google/gemini-1.5-pro": {"input": 1.25, "output": 5.0},
    "google/gemini-1.5-flash": {"input": 0.075, "output": 0.30},
}


def get_model_pricing(model: str) -> dict[str, float] | None:
    """Get pricing for a model based on pattern matching.

    Args:
        model: Model identifier (e.g., "anthropic/claude-sonnet-4-20250514")

    Returns:
        Dict with "input" and "output" prices per 1M tokens, or None if not found
    """
    for pattern, pricing in MODEL_PRICING.items():
        if model.startswith(pattern):
            return pricing
    return None


def extract_token_usage(log: EvalLog) -> dict[str, int]:
    """Extract token usage from the evaluation log.

    Args:
        log: The evaluation log

    Returns:
        Dictionary with input_tokens, output_tokens, and total_tokens
    """
    usage: dict[str, int] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "reasoning_tokens": 0,
    }

    if not log.stats or not log.stats.model_usage:
        return usage

    # Sum up usage across all models (usually just one)
    for model_usage in log.stats.model_usage.values():
        usage["input_tokens"] += model_usage.input_tokens or 0
        usage["output_tokens"] += model_usage.output_tokens or 0
        usage["total_tokens"] += model_usage.total_tokens or 0
        if model_usage.reasoning_tokens:
            usage["reasoning_tokens"] += model_usage.reasoning_tokens

    return usage


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Calculate the cost for a given token usage.

    Args:
        model: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD, or None if pricing not available
    """
    pricing = get_model_pricing(model)
    if not pricing:
        return None

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def extract_dataset_files(log: EvalLog) -> list[str]:
    """Extract the dataset files used in the evaluation from sample metadata."""
    dataset_files = set()

    # Try to extract from sample metadata
    for sample in log.samples or []:
        if sample.metadata:
            # Check if there's a puzzle_name or similar field that indicates the source
            if "puzzle_name" in sample.metadata:
                # Extract from sample ID which has format: filename_direction_number
                sample_id = sample.id or ""
                if "_across_" in sample_id or "_down_" in sample_id:
                    # Extract the filename part
                    base_name = sample_id.split("_across_")[0].split("_down_")[0]
                    dataset_files.add(f"data/benchmark/{base_name}.json")

    return sorted(dataset_files)


def extract_metrics(log: EvalLog) -> dict[str, float]:
    """Extract metrics from the evaluation log.

    Uses Inspect AI's built-in metrics including stderr.
    """
    metrics: dict[str, float] = {}

    if log.results and log.results.scores:
        for score in log.results.scores:
            # EvalScore has a metrics dict containing EvalMetric objects
            if hasattr(score, "metrics") and score.metrics:
                for metric_name, metric in score.metrics.items():
                    # EvalMetric has a value attribute
                    if hasattr(metric, "value"):
                        metrics[metric_name] = metric.value

    return metrics


def create_result_entry(log: EvalLog, log_path: Path) -> dict[str, Any]:
    """Create a result entry from an evaluation log.

    Args:
        log: The evaluation log
        log_path: Path to the log file

    Returns:
        Dictionary containing the result entry
    """
    # Extract run ID from log
    run_id = log.eval.run_id

    # Extract timestamp
    timestamp = datetime.fromisoformat(log.eval.created).isoformat()

    # Extract model
    model = log.eval.model

    # Extract task
    task = log.eval.task

    # Extract sample counts
    total_samples = len(log.samples) if log.samples else 0
    completed_samples = log.results.completed_samples if log.results else 0

    # Extract metrics (including stderr from Inspect)
    metrics = extract_metrics(log)

    # Extract dataset files
    dataset_files = extract_dataset_files(log)

    # Get versions
    inspect_version = "unknown"
    try:
        import inspect_ai

        inspect_version = inspect_ai.__version__
    except (ImportError, AttributeError):
        pass

    # Extract model_args from log
    model_args = log.eval.model_args if log.eval.model_args else {}

    # Extract token usage
    token_usage = extract_token_usage(log)

    # Calculate cost
    cost = calculate_cost(model, token_usage["input_tokens"], token_usage["output_tokens"])

    # Create result structure
    result: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": timestamp,
        "model": model,
        "task": task,
        "samples": {
            "total": total_samples,
            "completed": completed_samples,
        },
        "metrics": metrics,
        "model_args": model_args,
        "usage": {
            "input_tokens": token_usage["input_tokens"],
            "output_tokens": token_usage["output_tokens"],
            "total_tokens": token_usage["total_tokens"],
            "reasoning_tokens": token_usage["reasoning_tokens"],
            "cost_usd": cost,
        },
        "metadata": {
            "dataset_files": dataset_files,
            "eval_version": "0.1.0",
            "inspect_version": inspect_version,
            "log_file": str(log_path),
        },
    }

    return result


def get_model_results_path(model: str, output_dir: Path) -> Path:
    """Get the results file path for a specific model.

    Args:
        model: Model identifier
        output_dir: Output directory

    Returns:
        Path to the model's results file
    """
    # Create a safe filename from the model name
    model_slug = model.replace("/", "_").replace(":", "_")
    return output_dir / f"{model_slug}.jsonl"


def read_existing_results(results_path: Path) -> list[dict[str, Any]]:
    """Read existing results from a jsonlines file.

    Args:
        results_path: Path to the results file

    Returns:
        List of existing result entries
    """
    if not results_path.exists():
        return []

    results = []
    with open(results_path) as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))

    return results


def find_duplicate(
    new_result: dict[str, Any], existing_results: list[dict[str, Any]]
) -> int | None:
    """Find if a duplicate result exists.

    A duplicate is defined as having the same model, task, model_args, and dataset files.
    Runs with different model_args (e.g., different thinking budgets) are not duplicates.

    Args:
        new_result: The new result entry
        existing_results: List of existing results

    Returns:
        Index of duplicate if found, None otherwise
    """
    for idx, existing in enumerate(existing_results):
        # Check if model and task match
        if existing.get("model") != new_result.get("model") or existing.get(
            "task"
        ) != new_result.get("task"):
            continue

        # Check if samples match
        if existing.get("samples") != new_result.get("samples"):
            continue

        # Check if model_args match (different args = different run)
        existing_args = existing.get("model_args", {})
        new_args = new_result.get("model_args", {})
        if existing_args != new_args:
            continue

        # Check if dataset files match (ignore other metadata fields that may change)
        existing_files = existing.get("metadata", {}).get("dataset_files", [])
        new_files = new_result.get("metadata", {}).get("dataset_files", [])
        if existing_files != new_files:
            continue

        # Found a duplicate
        return idx

    return None


def save_eval_results(
    log_path: str | Path,
    output_dir: str | Path = "results",
    force: bool = False,
    include_incomplete: bool = False,
) -> Path | None:
    """Save evaluation results from an Inspect AI log file.

    Args:
        log_path: Path to the Inspect AI .eval log file
        output_dir: Directory to save results (default: "results")
        force: If True, skip duplicate check and override prompt
        include_incomplete: If True, save incomplete runs (default: False)

    Returns:
        Path to the saved results file, or None if skipped
    """
    log_path = Path(log_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read the evaluation log
    logger.info(f"Reading evaluation log from {log_path}")
    log = read_eval_log(log_path)

    # Create result entry
    result = create_result_entry(log, log_path)

    # Check if run is complete
    total = result["samples"]["total"]
    completed = result["samples"]["completed"]
    if completed < total and not include_incomplete:
        logger.warning(
            f"Skipping incomplete run: {completed}/{total} samples completed. "
            f"Use --include-incomplete to save anyway."
        )
        return None

    # Get the model-specific results file path
    results_path = get_model_results_path(result["model"], output_dir)

    # Read existing results
    existing_results = read_existing_results(results_path)

    # Check for duplicates
    duplicate_idx = find_duplicate(result, existing_results)

    if duplicate_idx is not None and not force:
        logger.warning("Found existing result with matching attributes:")
        logger.warning(f"  Timestamp: {existing_results[duplicate_idx]['timestamp']}")
        logger.warning(f"  Run ID: {existing_results[duplicate_idx]['run_id'][:8]}...")

        # Prompt user
        if click.confirm("Do you want to override the previous result?", default=True):
            # Replace the duplicate
            existing_results[duplicate_idx] = result
            logger.info("Overriding previous result")
        else:
            logger.info("Keeping previous result, appending new one")
            existing_results.append(result)
    else:
        # No duplicate or force mode, append
        if duplicate_idx is not None:
            logger.info("Force mode: overriding previous result")
            existing_results[duplicate_idx] = result
        else:
            existing_results.append(result)

    # Write all results back to file
    with open(results_path, "w") as f:
        for entry in existing_results:
            f.write(json.dumps(entry) + "\n")

    logger.info(f"Results saved to {results_path}")
    logger.info(f"  Model: {result['model']}")
    logger.info(f"  Task: {result['task']}")
    if result.get("model_args"):
        logger.info(f"  Model args: {result['model_args']}")

    # Log metrics
    metrics = result["metrics"]
    if "accuracy" in metrics:
        stderr_key = "accuracy_stderr" if "accuracy_stderr" in metrics else "stderr"
        stderr = metrics.get(stderr_key, 0.0)
        logger.info(f"  Accuracy: {metrics['accuracy']:.3f} ± {stderr:.3f}")

    logger.info(f"  Samples: {result['samples']['completed']}/{result['samples']['total']}")

    # Log token usage and cost
    usage = result.get("usage", {})
    if usage.get("total_tokens", 0) > 0:
        logger.info(f"  Tokens: {usage['input_tokens']:,} in / {usage['output_tokens']:,} out")
        if usage.get("reasoning_tokens", 0) > 0:
            logger.info(f"  Reasoning tokens: {usage['reasoning_tokens']:,}")
        if usage.get("cost_usd") is not None:
            logger.info(f"  Cost: ${usage['cost_usd']:.4f}")

    return results_path


@click.command()
@click.option(
    "--log",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the Inspect AI .eval log file",
)
@click.option(
    "--output-dir",
    default="results",
    type=click.Path(path_type=Path),
    help="Directory to save results (default: results)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip duplicate check and override prompt",
)
@click.option(
    "--include-incomplete",
    is_flag=True,
    help="Include incomplete runs (by default, only complete runs are saved)",
)
def main(log: Path, output_dir: Path, force: bool, include_incomplete: bool) -> None:
    """Save Inspect AI evaluation results to jsonlines format."""
    save_eval_results(log, output_dir, force, include_incomplete)


if __name__ == "__main__":
    main()
