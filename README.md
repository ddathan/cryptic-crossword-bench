# Cryptic Crossword Evaluation

An LLM evaluation benchmark for testing the ability to solve cryptic crossword puzzles.

## Overview

This project extracts cryptic crossword clues and answers from PDF and PNG files to create a structured benchmark dataset for evaluating Large Language Models on their cryptic crossword solving abilities.

## Features

- Extract clues from crossword PDF files using layout-aware parsing
- Extract answers from completed crossword images using Claude's vision API
- Generate structured JSON benchmark data combining clues and answers
- Support for both standard cryptic and quick cryptic crosswords
- Inspect AI evaluation framework for testing LLMs on cryptic crossword solving
- Custom scoring with exact match (normalized for case and spacing)
- Comprehensive metadata tracking (puzzle name, date, clue direction, etc.)

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
# Run evaluation on all crosswords
uv run inspect eval eval/cryptic_crossword_eval.py

# Run on a specific crossword
uv run inspect eval eval/cryptic_crossword_eval.py@cryptic_crossword_single \
  --benchmark_file data/benchmark/crossword-cryptic-20260109-80222.json

# Use a specific model (requires ANTHROPIC_API_KEY)
uv run inspect eval eval/cryptic_crossword_eval.py --model anthropic/claude-sonnet-4-20250514

# View results in web UI
uv run inspect view
```

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
│   └── run_eval_example.py        # Example: Run evaluation programmatically
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

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
