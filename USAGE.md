# Usage Guide

## Quick Start

Once you have credits in your Anthropic account, run the complete extraction pipeline:

```bash
uv run python -m extraction.run_extraction
```

This will:
1. Extract clues from all PDF files in `data/raw/`
2. Use Claude's vision API to extract answers from completed crossword images
3. Generate benchmark JSON files in `data/benchmark/`

## Output Structure

Each benchmark file contains:

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
    },
    ...
  },
  "down": {
    "2": {
      "clue": "\"Meet\" me on the waves?",
      "answer_length": [5, 3],
      "answer": "GREETGEM"
    },
    ...
  }
}
```

## Using the Benchmark

### Example: Evaluating an LLM

```python
import json
from pathlib import Path

# Load a crossword benchmark
with open("data/benchmark/crossword-cryptic-20260109-80222.json") as f:
    crossword = json.load(f)

# Test your LLM on each clue
for clue_num, clue_data in crossword["across"].items():
    clue = clue_data["clue"]
    answer_length = clue_data["answer_length"]
    expected_answer = clue_data["answer"]

    # Prompt your LLM
    prompt = f"""Solve this cryptic crossword clue:

Clue: {clue}
Answer length: {'-'.join(str(n) for n in answer_length)} letters

Provide only the answer, no explanation."""

    # Get LLM response
    llm_answer = your_llm_function(prompt)

    # Evaluate
    correct = llm_answer.upper().replace(" ", "") == expected_answer
    print(f"{clue_num} ACROSS: {'✓' if correct else '✗'}")
```

### Evaluation Metrics

Consider tracking:
- **Exact match accuracy**: Percentage of clues solved correctly
- **Partial credit**: Edit distance or character overlap
- **By difficulty**: Compare performance on Quick Cryptic vs full Cryptic
- **By clue type**: Track accuracy on different cryptic clue patterns
  - Anagrams
  - Hidden words
  - Homophones
  - Reversals
  - Container clues
  - etc.

## Adding More Crosswords

1. Place PDF files with clues in `data/raw/`
2. Place corresponding completed crossword images in `data/raw/` with `-complete.png` suffix
3. Ensure filenames match (e.g., `puzzle-123.pdf` and `puzzle-123-complete.png`)
4. Run `uv run python -m extraction.run_extraction`

## Troubleshooting

### API Credits Issue
```
Error: Your credit balance is too low to access the Anthropic API
```
Solution: Add credits at https://console.anthropic.com/settings/billing

### Clues Not Extracting Correctly
The PDF parser works best with two-column layouts where ACROSS clues are on the left and DOWN clues are on the right. If your PDFs have a different layout, you may need to modify `extraction/extract_clues.py`.

### Missing Answers
If Claude doesn't extract all answers, check:
- Image quality (should be clear and readable)
- Grid numbers are visible
- Image is not too compressed

You can adjust the Claude prompt in `extraction/extract_answers.py` to improve accuracy.
