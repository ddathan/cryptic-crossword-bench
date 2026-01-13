"""Build results.json for the web dashboard from JSONL result files."""

import json
from pathlib import Path

from loguru import logger

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
OUTPUT_FILE = Path(__file__).parent / "results.json"


def get_best_result(results: list[dict]) -> dict:
    """Get the best result from a list of results for the same model+args combination.

    Selection criteria (in order):
    1. Highest number of completed samples
    2. Most recent timestamp
    """
    if not results:
        return {}

    return max(results, key=lambda r: (r.get("samples", {}).get("completed", 0), r["timestamp"]))


def create_result_key(result: dict) -> str:
    """Create a unique key for a model+args combination."""
    model = result.get("model", "")
    model_args = result.get("model_args", {})
    # Sort args for consistent key
    args_str = json.dumps(model_args, sort_keys=True) if model_args else ""
    return f"{model}|{args_str}"


def load_all_results() -> list[dict]:
    """Load all results from JSONL files in the results directory."""
    all_results: list[dict] = []

    if not RESULTS_DIR.exists():
        return all_results

    for jsonl_file in RESULTS_DIR.glob("*.jsonl"):
        with open(jsonl_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        result = json.loads(line)
                        all_results.append(result)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse line in {jsonl_file}")

    return all_results


def deduplicate_results(results: list[dict]) -> list[dict]:
    """Deduplicate results, keeping the best run for each model+args combination."""
    # Group by model+args
    groups: dict[str, list[dict]] = {}
    for result in results:
        key = create_result_key(result)
        if key not in groups:
            groups[key] = []
        groups[key].append(result)

    # Select best from each group
    deduplicated = []
    for group_results in groups.values():
        best = get_best_result(group_results)
        if best:
            deduplicated.append(best)

    # Sort by accuracy (descending)
    deduplicated.sort(
        key=lambda r: r.get("metrics", {}).get("accuracy", 0),
        reverse=True,
    )

    return deduplicated


def format_model_name(model: str) -> str:
    """Format model name for display."""
    # Remove provider prefix for cleaner display
    if "/" in model:
        return model.split("/", 1)[1]
    return model


def build_web_results() -> dict:
    """Build the results data structure for the web dashboard."""
    all_results = load_all_results()
    deduplicated = deduplicate_results(all_results)

    # Format for web display
    web_results = []
    for result in deduplicated:
        model_args = result.get("model_args", {})
        metrics = result.get("metrics", {})

        web_result = {
            "model": result.get("model", "Unknown"),
            "model_display": format_model_name(result.get("model", "Unknown")),
            "accuracy": metrics.get("accuracy", 0),
            "stderr": metrics.get("accuracy_stderr", metrics.get("stderr", 0)),
            "samples_completed": result.get("samples", {}).get("completed", 0),
            "samples_total": result.get("samples", {}).get("total", 0),
            "model_args": model_args,
            "timestamp": result.get("timestamp", ""),
            "run_id": result.get("run_id", "")[:8],
        }
        web_results.append(web_result)

    return {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "total_results": len(web_results),
        "results": web_results,
    }


def main() -> None:
    """Generate results.json for the web dashboard."""
    logger.info(f"Loading results from {RESULTS_DIR}")
    web_data = build_web_results()

    logger.info(f"Found {web_data['total_results']} unique model configurations")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(web_data, f, indent=2)

    logger.info(f"Results written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
