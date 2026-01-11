# Evaluation Results

This directory contains evaluation results for different models on the cryptic crossword benchmark.

## Format

Each evaluation run is stored as a separate JSON file with the following structure:

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
    "stderr": 0.048
  },
  "metadata": {
    "dataset_files": [
      "data/benchmark/crossword-cryptic-20260109-80222.json",
      "data/benchmark/crossword-quick-cryptic-20260109-80229.json"
    ],
    "eval_version": "0.1.0",
    "inspect_version": "0.3.160"
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
- `metrics.accuracy`: Overall accuracy score (0-1)
- `metrics.stderr`: Standard error of the accuracy metric
- `metadata`: Additional metadata about the run
  - `dataset_files`: List of benchmark files used
  - `eval_version`: Version of the evaluation code
  - `inspect_version`: Version of Inspect AI used

## Prerequisites

Before running evaluations, ensure you have benchmark data:

```bash
# Extract crossword data first
uv run python -m extraction.run_extraction
```

This creates benchmark files in `data/benchmark/` which are used by the evaluation.

## Usage

Results are automatically saved when using the `run_and_save.py` script:

```bash
# Run evaluation and automatically save results
uv run python eval/run_and_save.py --model anthropic/claude-sonnet-4-20250514

# Or run inspection and save from log separately
uv run inspect eval eval/cryptic_crossword_eval.py --model anthropic/claude-sonnet-4-20250514
uv run python eval/save_results.py --log logs/LATEST_LOG_FILE.eval
```

## Deduplication

When multiple runs exist for the same model+task combination, the run with the highest number of completed samples should be used for visualization. This ensures the most complete evaluation is displayed.
