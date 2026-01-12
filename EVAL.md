# Running the Cryptic Crossword Evaluation

This project includes an Inspect AI evaluation for testing LLMs on cryptic crossword solving.

## Quick Start

### Run evaluation and save results (recommended)

```bash
# Run evaluation and automatically save results
uv run python eval/run_and_save.py --model anthropic/claude-sonnet-4-20250514

# Run multiple models simultaneously
uv run python eval/run_and_save.py \
  -m anthropic/claude-sonnet-4-20250514 \
  -m anthropic/claude-opus-4-20250514
```

This will:
1. Run the evaluation (supports multiple models simultaneously)
2. Automatically save results to `results/` directory in jsonlines format
3. Results include accuracy, stderr, sample counts, and metadata
4. Each model's results are saved in a single file for easy tracking

### Run evaluation only (without saving)

```bash
uv run inspect eval eval/cryptic_crossword_eval.py
```

### Run on a specific crossword

```bash
uv run inspect eval eval/cryptic_crossword_eval.py@cryptic_crossword_single \
  --benchmark_file data/benchmark/crossword-cryptic-20260109-80222.json
```

### Use a specific model

```bash
# Use Claude models (requires ANTHROPIC_API_KEY environment variable)
uv run inspect eval eval/cryptic_crossword_eval.py --model anthropic/claude-sonnet-4-20250514
uv run inspect eval eval/cryptic_crossword_eval.py --model anthropic/claude-opus-4-20250514

# Use OpenAI models (requires OPENAI_API_KEY environment variable)
uv run inspect eval eval/cryptic_crossword_eval.py --model openai/gpt-4

# Use a mock model for testing
uv run inspect eval eval/cryptic_crossword_eval.py --model mockllm/model
```

### Limit the number of samples

```bash
uv run inspect eval eval/cryptic_crossword_eval.py --limit 10
```

## Evaluation Structure

The evaluation:
1. Loads cryptic crossword clues from JSON files in `data/benchmark/`
2. Prompts the model with each clue and the answer length
3. Scores based on exact match (case-insensitive, alphanumeric only)
4. Tracks metadata including puzzle name, date, clue number, and direction

## Available Tasks

### `cryptic_crossword`
Evaluates the model on all crossword puzzles in the `data/benchmark/` directory.

```bash
uv run inspect eval eval/cryptic_crossword_eval.py
```

### `cryptic_crossword_single`
Evaluates the model on a single specified crossword puzzle.

```bash
uv run inspect eval eval/cryptic_crossword_eval.py@cryptic_crossword_single \
  --benchmark_file data/benchmark/crossword-quick-cryptic-20260109-80229.json
```

## Scoring

The evaluation uses a custom scorer that:
- Normalizes both the model's answer and the expected answer
- Removes spaces, punctuation, and converts to uppercase
- Checks for exact match
- Reports accuracy across all clues

## Example Output

```
Target: cryptic_crossword
Samples: 50
Accuracy: 0.24
```

The evaluation will also generate a detailed log showing:
- Each clue
- The model's answer
- The expected answer
- Whether it was correct

## Running Programmatically

You can also run the evaluation from Python code:

```python
from inspect_ai import eval
from eval.cryptic_crossword_eval import cryptic_crossword

# Run evaluation
logs = eval(
    cryptic_crossword(),
    model="anthropic/claude-sonnet-4-20250514",
    limit=10
)

# Access results
log = logs[0]
print(f"Accuracy: {log.results.scores[0].value}")
```

See `eval/run_eval_example.py` for a complete example.

## Customization

### Modify the prompt

Edit the `prompt` variable in `load_crossword_samples()` in `eval/cryptic_crossword_eval.py` to change how clues are presented to the model.

### Change the scoring logic

Edit the `cryptic_scorer()` function to implement different scoring rules (e.g., partial credit for close matches).

### Add new metadata

Extend the `metadata` dictionary in `load_crossword_samples()` to track additional information about each clue.

## Saving and Tracking Results

### Automatic Saving (Recommended)

Use the `run_and_save.py` script to automatically save results after each evaluation:

```bash
# Run and save for a specific model
uv run python eval/run_and_save.py --model anthropic/claude-sonnet-4-20250514

# Run multiple models simultaneously
uv run python eval/run_and_save.py \
  -m anthropic/claude-sonnet-4-20250514 \
  -m anthropic/claude-opus-4-20250514

# Run with model arguments (e.g., thinking budget)
uv run python eval/run_and_save.py \
  --model anthropic/claude-sonnet-4-20250514 \
  --model-arg thinking_budget=10000

# Run with multiple model arguments
uv run python eval/run_and_save.py \
  --model anthropic/claude-sonnet-4-20250514 \
  -a thinking_budget=10000 \
  -a temperature=0.5

# Run on a specific benchmark file
uv run python eval/run_and_save.py --model anthropic/claude-opus-4-20250514 \
  --benchmark-file data/benchmark/crossword-cryptic-20260109-80222.json

# Test with limited samples
uv run python eval/run_and_save.py --model mockllm/model --limit 10

# Force overwrite without prompting
uv run python eval/run_and_save.py --model mockllm/model --force
```

### Manual Saving

If you've already run an evaluation, you can save the results manually:

```bash
# Save from the latest log file
uv run python eval/save_results.py --log logs/2026-01-10T12-34-56+00-00_cryptic-crossword_ABC123.eval

# Force overwrite without prompting for duplicates
uv run python eval/save_results.py --log logs/LATEST.eval --force
```

### Results Format

Results are saved in `results/` as **jsonlines** files (`.jsonl`), with one file per model:
- **Format**: One JSON object per line, each representing a single evaluation run
- **Filename**: Based on model identifier (e.g., `anthropic_claude-sonnet-4-20250514.jsonl`)
- **Deduplication**: Automatically detects and prompts for duplicate results (same model, task, model_args)
- **Model Args**: Stores model arguments (e.g., thinking budget) for each run
- **Metrics**: Accuracy and standard error from Inspect AI's built-in metrics
- **Metadata**: Model, task, timestamp, dataset files, versions

Example filename: `anthropic_claude-sonnet-4-20250514.jsonl`

See `results/README.md` for detailed format documentation.

### Viewing Saved Results

```bash
# List all saved results
ls results/*.jsonl

# View all results for a model
cat results/anthropic_claude-sonnet-4-20250514.jsonl

# Read results programmatically
python -c "
import json
with open('results/anthropic_claude-sonnet-4-20250514.jsonl') as f:
    for line in f:
        result = json.loads(line)
        print(f'{result[\"timestamp\"]}: {result[\"metrics\"][\"accuracy\"]:.3f}')
"
```

The results are version-controlled in git, making it easy to track model performance over time. The jsonlines format is git-friendly and shows clear diffs when results change.

## View Results

After running an evaluation, view the results in Inspect AI's web interface:

```bash
uv run inspect view
```

This opens a web interface showing detailed results for all evaluations.

## Tips for Better Results

1. Use Claude Opus or Sonnet models for best performance on cryptic crosswords
2. Adjust the system message in the task to provide more context about cryptic clue types
3. Consider adding few-shot examples in the prompt
4. Experiment with temperature settings (lower for more consistent answers)

## Example: Compare Multiple Models

```bash
# Run and save multiple models simultaneously (recommended)
uv run python eval/run_and_save.py \
  -m anthropic/claude-sonnet-4-20250514 \
  -m anthropic/claude-opus-4-20250514 \
  -m openai/gpt-4

# Or run them separately via Inspect
uv run inspect eval eval/cryptic_crossword_eval.py --model anthropic/claude-sonnet-4-20250514
uv run inspect eval eval/cryptic_crossword_eval.py --model anthropic/claude-opus-4-20250514
uv run inspect eval eval/cryptic_crossword_eval.py --model openai/gpt-4

# View comparison in web UI
uv run inspect view
```

## Troubleshooting

### API Key Issues
Make sure your API key is set in the `.env` file:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### File Not Found
Ensure you've run the data extraction pipeline first:
```bash
uv run python -m extraction.run_extraction
```

### Import Errors
Make sure inspect-ai is installed:
```bash
uv sync
```
