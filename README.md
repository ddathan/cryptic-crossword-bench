# Cryptic Crossword Evaluation

A benchmark to test LLM's abilility to solve cryptic crosswords

## Overview

This benchmark evaluates how well LLMs can solve cryptic crossword clues. At the start of 2025 I decided to try to get better at cryptic crosswords. Naturally, I attempted to use LLMs to help me by getting them to explain the clues and answers when I was stuck. What I found was that (at that time) LLMs were pretty bad at solving cryptic crosswords - they would often take illogical reasoning steps resulting in the wrong answer, or even when given the answer they would come up with spurious reasoning as to how to get there.

As of the start of 2026... they are a lot better, but still not perfect. See the results on the [website](https://ddathan.github.io/cryptic-crossword-bench/)

## Disclaimer

This was a side project with the majority of code written by Claude Code, as such there may be errors.

## TODO
- [ ] Test models at varying thinking levels / inference budgets
- [ ] Add plot to website with x-axis showing token / cost
- [ ] Test latest closed source models (Opus 4.6, GPT-codex 5.3)
- [ ] Add SOTA open source models as a comparison

## Setup

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Anthropic API key

### Installation

1. Clone the repository:
```bash
cd cryptic-crossword-eval
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set up your Anthropic API key:
```bash
cp .env.example .env
# Edit .env and add your API key
```

## Usage

### Complete Extraction Pipeline

Run the main extraction script to process all crossword files:

```bash
uv run python -m extraction.run_extraction
```

This will:
1. Extract clues from PDF files in `data/raw/`
2. Extract answers from completed crossword PNG images using Claude API
3. Generate benchmark JSON files in `data/benchmark/`

### Individual Scripts

Extract clues only:
```bash
uv run python -m extraction.extract_clues
```

Extract answers only (requires clues to be extracted first):
```bash
uv run python -m extraction.extract_answers
```

### Running the Evaluation

Once you have benchmark data, evaluate LLMs using Inspect AI:

```bash
# Run evaluation and automatically save results (recommended)
uv run python eval/run_and_save.py --model anthropic/claude-sonnet-4-20250514

# Run multiple models simultaneously
uv run python eval/run_and_save.py \
  -m anthropic/claude-sonnet-4-20250514 \
  -m anthropic/claude-opus-4-20250514

# Or run without saving
uv run inspect eval eval/cryptic_crossword_eval.py --model anthropic/claude-sonnet-4-20250514

# View results in web UI
uv run inspect view
```

Results are automatically saved to the `results/` directory in jsonlines format:
- One file per model (e.g., `anthropic_claude-sonnet-4-20250514.jsonl`)
- Each line contains a complete evaluation run
- Accuracy and standard error from Inspect AI
- Sample counts and metadata

See [EVAL.md](EVAL.md) for detailed evaluation documentation.

## Data Format

### Input Files

Place your crossword files in the `data/raw/` directory:
- PDF files containing clues (e.g., `crossword-cryptic-20260109-80222.pdf`)
- PNG files with completed grids (e.g., `crossword-cryptic-20260109-80222-complete.png`)

### Output Format

Benchmark data is saved as JSON with the following structure:

```json
{
  "metadata": {
    "date": "Friday, 09 January 2026",
    "puzzle_name": "Times Cryptic No 29435"
  },
  "across": {
    "1": {
      "clue": "The last thing batter needs to stop collapse?",
      "answer_length": [8],
      "answer": "GROUNDER"
    }
  },
  "down": {
    "2": {
      "clue": "\"Meet\" me on the waves?",
      "answer_length": [5, 3],
      "answer": "GREETGEM"
    }
  }
}
```

## Project Structure

```
cryptic-crossword-eval/
├── data/
│   ├── raw/                       # Input crossword PDFs and images
│   ├── extracted/                 # Intermediate clue extraction results
│   └── benchmark/                 # Final benchmark JSON files
├── extraction/
│   ├── extract_clues.py           # PDF clue extraction
│   ├── extract_answers.py         # Image answer extraction using Claude
│   └── run_extraction.py          # Main extraction pipeline
├── eval/
│   ├── cryptic_crossword_eval.py  # Inspect AI evaluation
│   ├── run_and_save.py            # Run evaluation and save results
│   ├── save_results.py            # Save results from eval logs
│   └── run_eval_example.py        # Example: Run evaluation programmatically
├── results/                       # Saved evaluation results (version controlled)
├── pyproject.toml                 # Project dependencies
├── README.md                      # This file
└── EVAL.md                        # Evaluation documentation
```

## Development

### Linting and Formatting

This project uses ruff for linting and formatting:

```bash
uv run ruff check .
uv run ruff format .
```

### Type Checking

Type checking with mypy:

```bash
uv run mypy .
```

### Pre-commit Hooks

Pre-commit hooks are configured to run linting and formatting automatically:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```
