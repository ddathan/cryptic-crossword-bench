# Evaluation Results

This directory contains evaluation results for different models on the cryptic crossword benchmark.

## Format

Results are stored in jsonlines format (`.jsonl`), with one file per model. Each line in a file represents a single evaluation run.

### File Naming

Files are named based on the model identifier:
- `anthropic_claude-sonnet-4-20250514.jsonl` - Results for Claude Sonnet
- `anthropic_claude-opus-4-20250514.jsonl` - Results for Claude Opus

### Result Entry Structure

Each line in a jsonlines file contains a JSON object with the following structure:

```json
{
  "run_id": "unique-run-identifier",
  "timestamp": "2026-01-10T12:34:56.789Z",
  "model": "anthropic/claude-sonnet-4-20250514",
  "task": "cryptic_crossword",
  "samples": {
    "total": 51,
    "completed": 51
  },
  "metrics": {
    "accuracy": 0.137,
    "accuracy_stderr": 0.048
  },
  "model_args": {
    "thinking_budget": 10000
  },
  "metadata": {
    "dataset_files": [
      "data/benchmark/crossword-cryptic-20260109-80222.json",
      "data/benchmark/crossword-quick-cryptic-20260109-80229.json"
    ],
    "eval_version": "0.1.0",
    "inspect_version": "0.3.160",
    "log_file": "logs/2026-01-10_12-34-56_example.eval"
  }
}
```

## Fields

- `run_id`: Unique identifier for this evaluation run (derived from Inspect AI log)
- `timestamp`: ISO 8601 timestamp of when the evaluation was run
- `model`: Model identifier used for the evaluation
- `task`: Name of the Inspect AI task
- `samples.total`: Total number of samples in the dataset
- `samples.completed`: Number of samples successfully completed
- `metrics`: Dictionary of metrics from the evaluation
  - `accuracy`: Overall accuracy score (0-1)
  - `accuracy_stderr`: Standard error of the accuracy metric (from Inspect AI)
  - Additional metrics may be present depending on the evaluation
- `model_args`: Model arguments passed to the evaluation (e.g., thinking budget)
  - Empty object `{}` if no model args were specified
  - Used for deduplication: runs with different model_args are not considered duplicates
- `metadata`: Additional metadata about the run
  - `dataset_files`: List of benchmark files used
  - `eval_version`: Version of the evaluation code
  - `inspect_version`: Version of Inspect AI used
  - `log_file`: Path to the original Inspect AI log file

## Prerequisites

Before running evaluations, ensure you have benchmark data:

```bash
# Extract crossword data first
uv run python -m extraction.run_extraction
```

This creates benchmark files in `data/benchmark/` which are used by the evaluation.

## Usage

### Running Evaluations

Results are automatically saved when using the `run_and_save.py` script:

```bash
# Run evaluation with a single model
uv run python eval/run_and_save.py --model anthropic/claude-sonnet-4-20250514

# Run evaluation with multiple models simultaneously
uv run python eval/run_and_save.py \
  -m anthropic/claude-sonnet-4-20250514 \
  -m anthropic/claude-opus-4-20250514

# Run with model arguments (e.g., thinking budget)
uv run python eval/run_and_save.py \
  --model anthropic/claude-sonnet-4-20250514 \
  --model-arg thinking_budget=10000

# Run with a specific benchmark file
uv run python eval/run_and_save.py \
  --model anthropic/claude-sonnet-4-20250514 \
  --benchmark-file data/benchmark/crossword-cryptic-20260109-80222.json
```

### Manually Saving Results

You can also run Inspect and save results separately:

```bash
# Run inspection
uv run inspect eval eval/cryptic_crossword_eval.py --model anthropic/claude-sonnet-4-20250514

# Save from log
uv run python eval/save_results.py --log logs/LATEST_LOG_FILE.eval
```

### Duplicate Detection

The saving system automatically detects duplicate results (same model, task, model_args, samples, and dataset files). Runs with different model_args are considered distinct and will not trigger duplicate detection. When a duplicate is found:

1. You'll be prompted whether to override the previous result (default: yes)
2. If you choose "yes", the old result is replaced
3. If you choose "no", both results are kept

Use the `--force` flag to automatically override without prompting:

```bash
uv run python eval/save_results.py --log logs/example.eval --force
```

## Reading Results

To read and analyze results programmatically:

```python
import json
from pathlib import Path

# Read all results for a model
model_slug = "anthropic_claude-sonnet-4-20250514"
results_path = Path(f"results/{model_slug}.jsonl")

results = []
with open(results_path) as f:
    for line in f:
        results.append(json.loads(line))

# Access individual runs
for result in results:
    print(f"Run {result['run_id'][:8]}: {result['metrics']['accuracy']:.3f}")
```

## Benefits

1. **Version Control**: Results are committed to git, tracking performance over time
2. **Single File Per Model**: All runs for a model are in one file for easy tracking
3. **Git-Friendly Format**: Jsonlines format shows clear diffs when results change
4. **Deduplication**: Prevents accidental duplicate entries
5. **Multiple Models**: Support for running and tracking multiple models simultaneously
6. **Reproducibility**: Full metadata enables reproducing exact evaluation conditions
7. **Future Visualization**: Structured format ready for web-based plotting/comparison
