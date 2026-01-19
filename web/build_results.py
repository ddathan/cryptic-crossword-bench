"""Build results.json for the web dashboard from JSONL result files."""

import json
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"
OUTPUT_FILE = Path(__file__).parent / "results.json"

# API pricing per 1M tokens (USD)
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Anthropic models
    "anthropic/claude-opus-4": {"input": 15.0, "output": 75.0},
    "anthropic/claude-sonnet-4": {"input": 3.0, "output": 15.0},
    "anthropic/claude-haiku-4": {"input": 0.80, "output": 4.0},
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
}


def get_model_pricing(model: str) -> dict[str, float] | None:
    """Get pricing for a model based on pattern matching."""
    for pattern, pricing in MODEL_PRICING.items():
        if model.startswith(pattern):
            return pricing
    return None


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Calculate the cost for a given token usage."""
    pricing = get_model_pricing(model)
    if not pricing:
        return None
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def extract_usage_from_log(log_file: str) -> dict[str, int | float | None]:
    """Extract token usage from an Inspect AI log file.

    Args:
        log_file: Path to the log file (relative or absolute)

    Returns:
        Dictionary with token counts and cost, or empty values if extraction fails
    """
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    reasoning_tokens = 0

    # Try to find the log file
    log_path = Path(log_file)
    if not log_path.is_absolute():
        log_path = PROJECT_ROOT / log_file

    if not log_path.exists():
        # Try looking in the logs directory with just the filename
        log_path = LOGS_DIR / Path(log_file).name

    if not log_path.exists():
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "reasoning_tokens": 0,
            "cost_usd": None,
        }

    try:
        from inspect_ai.log import read_eval_log

        log = read_eval_log(str(log_path))

        if log.stats and log.stats.model_usage:
            for model_usage in log.stats.model_usage.values():
                input_tokens += model_usage.input_tokens or 0
                output_tokens += model_usage.output_tokens or 0
                total_tokens += model_usage.total_tokens or 0
                if model_usage.reasoning_tokens:
                    reasoning_tokens += model_usage.reasoning_tokens

    except Exception as e:
        print(f"Warning: Could not extract usage from {log_path}: {e}")

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "reasoning_tokens": reasoning_tokens,
        "cost_usd": None,
    }


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


def is_complete_run(result: dict) -> bool:
    """Check if a result represents a complete evaluation run."""
    samples = result.get("samples", {})
    total: int = samples.get("total", 0)
    completed: int = samples.get("completed", 0)
    return total > 0 and completed == total


def load_all_results() -> list[dict]:
    """Load all results from JSONL files in the results directory.

    Only loads complete runs (where completed == total samples).
    """
    all_results: list[dict] = []
    skipped_incomplete = 0

    if not RESULTS_DIR.exists():
        return all_results

    for jsonl_file in RESULTS_DIR.glob("*.jsonl"):
        with open(jsonl_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        result = json.loads(line)
                        if is_complete_run(result):
                            all_results.append(result)
                        else:
                            skipped_incomplete += 1
                    except json.JSONDecodeError:
                        print(f"Warning: Could not parse line in {jsonl_file}")

    if skipped_incomplete > 0:
        print(f"Skipped {skipped_incomplete} incomplete run(s)")

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
        usage = result.get("usage", {})

        # If usage is missing or empty, try to extract from log file
        total_tokens = usage.get("total_tokens")
        if not usage or (isinstance(total_tokens, (int, float)) and total_tokens == 0):
            log_file = result.get("metadata", {}).get("log_file", "")
            if log_file:
                usage = extract_usage_from_log(log_file)
                # Calculate cost if we have tokens
                model = result.get("model", "")
                extracted_total = usage.get("total_tokens", 0)
                if isinstance(extracted_total, (int, float)) and extracted_total > 0:
                    input_tok = usage.get("input_tokens", 0)
                    output_tok = usage.get("output_tokens", 0)
                    if isinstance(input_tok, int) and isinstance(output_tok, int):
                        usage["cost_usd"] = calculate_cost(model, input_tok, output_tok)

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
            # Token usage and cost
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "reasoning_tokens": usage.get("reasoning_tokens", 0),
            "cost_usd": usage.get("cost_usd"),
        }
        web_results.append(web_result)

    return {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "total_results": len(web_results),
        "results": web_results,
    }


def main() -> None:
    """Generate results.json for the web dashboard."""
    print(f"Loading results from {RESULTS_DIR}")
    web_data = build_web_results()

    print(f"Found {web_data['total_results']} unique model configurations")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(web_data, f, indent=2)

    print(f"Results written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
