"""Save Inspect AI evaluation results to the results directory."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from inspect_ai.log import EvalLog, read_eval_log
from loguru import logger


def calculate_stderr(accuracy: float, n: int) -> float:
    """Calculate standard error for accuracy metric.

    Uses the formula: stderr = sqrt(p * (1-p) / n)
    where p is the accuracy and n is the sample size.
    """
    if n == 0:
        return 0.0
    stderr: float = (accuracy * (1 - accuracy) / n) ** 0.5
    return stderr


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


def save_eval_results(log_path: str | Path, output_dir: str | Path = "results") -> Path:
    """Save evaluation results from an Inspect AI log file.

    Args:
        log_path: Path to the Inspect AI .eval log file
        output_dir: Directory to save results (default: "results")

    Returns:
        Path to the saved results file
    """
    log_path = Path(log_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read the evaluation log
    logger.info(f"Reading evaluation log from {log_path}")
    log = read_eval_log(log_path)

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
    completed_samples = log.results.samples_completed if log.results else 0

    # Extract metrics
    accuracy = 0.0
    if log.results and log.results.scores:
        # Find the accuracy score
        for score in log.results.scores:
            if score.name == "accuracy":
                accuracy = score.value
                break

    # Calculate stderr
    stderr = calculate_stderr(accuracy, completed_samples)

    # Extract dataset files
    dataset_files = extract_dataset_files(log)

    # Get versions
    inspect_version = "unknown"
    try:
        import inspect_ai

        inspect_version = inspect_ai.__version__
    except (ImportError, AttributeError):
        pass

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
        "metrics": {
            "accuracy": accuracy,
            "stderr": stderr,
        },
        "metadata": {
            "dataset_files": dataset_files,
            "eval_version": "0.1.0",
            "inspect_version": inspect_version,
            "log_file": str(log_path),
        },
    }

    # Generate output filename
    # Format: YYYY-MM-DD_HH-MM-SS_model-name_run-id.json
    timestamp_str = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d_%H-%M-%S")
    model_slug = model.replace("/", "_").replace(":", "_")
    output_filename = f"{timestamp_str}_{model_slug}_{run_id[:8]}.json"
    output_path = output_dir / output_filename

    # Save results
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Results saved to {output_path}")
    logger.info(f"  Model: {model}")
    logger.info(f"  Task: {task}")
    logger.info(f"  Accuracy: {accuracy:.3f} ± {stderr:.3f}")
    logger.info(f"  Samples: {completed_samples}/{total_samples}")

    return output_path


def main() -> None:
    """CLI entrypoint for saving results."""
    import argparse

    parser = argparse.ArgumentParser(description="Save Inspect AI evaluation results")
    parser.add_argument(
        "--log",
        required=True,
        help="Path to the Inspect AI .eval log file",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to save results (default: results)",
    )

    args = parser.parse_args()

    save_eval_results(args.log, args.output_dir)


if __name__ == "__main__":
    main()
