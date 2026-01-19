"""Inspect AI evaluation for cryptic crossword solving."""

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import generate, system_message
from loguru import logger

from ._prompts import SYSTEM_PROMPT, format_clue_prompt

# Get the project root directory (parent of the eval folder)
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from .env file
load_dotenv(PROJECT_ROOT / ".env")


def normalize_answer(answer: str) -> str:
    """Normalize an answer by converting to uppercase and removing spaces/punctuation."""
    return "".join(c for c in answer.upper() if c.isalnum())


def extract_answer_from_tags(completion: str) -> str:
    """Extract the answer from <answer></answer> tags in the completion.

    Args:
        completion: The full model completion text

    Returns:
        The extracted answer, or the full completion if no tags found
    """
    # Look for <answer>...</answer> pattern (case-insensitive)
    pattern = r"<answer>(.*?)</answer>"
    match = re.search(pattern, completion, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(1).strip()

    # Fallback: return the full completion stripped
    return completion.strip()


@scorer(metrics=[accuracy(), stderr()])  # type: ignore[arg-type]
def cryptic_scorer() -> Callable[[Any, Target], Score]:
    """Score cryptic crossword answers with exact match after normalization."""

    async def score(state: Any, target: Target) -> Score:
        # Get the full model completion
        full_completion = state.output.completion

        # Extract the answer from <answer> tags
        model_answer = extract_answer_from_tags(full_completion)

        # Normalize both answers
        normalized_model = normalize_answer(model_answer)
        normalized_target = normalize_answer(target.text)

        # Check for exact match
        correct = normalized_model == normalized_target

        return Score(
            value=correct,
            answer=model_answer,
            explanation=f"Model: {model_answer} | Expected: {target.text} | Match: {correct}",
        )

    return score  # type: ignore[return-value]


def load_crossword_samples(benchmark_file: Path) -> list[Sample]:
    """Load crossword clues as Inspect AI samples from a benchmark JSON file."""
    with open(benchmark_file) as f:
        data = json.load(f)

    samples = []
    metadata = data.get("metadata", {})
    puzzle_name = metadata.get("puzzle_name", "Unknown")
    puzzle_date = metadata.get("date", "Unknown")

    # Process ACROSS clues
    for clue_num, clue_data in data.get("across", {}).items():
        clue_text = clue_data["clue"]
        answer_length = clue_data["answer_length"]
        answer = clue_data["answer"]

        # Create the prompt using the template
        prompt = format_clue_prompt(clue_text, answer_length)

        samples.append(
            Sample(
                input=prompt,
                target=answer,
                id=f"{benchmark_file.stem}_across_{clue_num}",
                metadata={
                    "clue_number": clue_num,
                    "direction": "across",
                    "puzzle_name": puzzle_name,
                    "puzzle_date": puzzle_date,
                    "answer_length": answer_length,
                },
            )
        )

    # Process DOWN clues
    for clue_num, clue_data in data.get("down", {}).items():
        clue_text = clue_data["clue"]
        answer_length = clue_data["answer_length"]
        answer = clue_data["answer"]

        # Create the prompt using the template
        prompt = format_clue_prompt(clue_text, answer_length)

        samples.append(
            Sample(
                input=prompt,
                target=answer,
                id=f"{benchmark_file.stem}_down_{clue_num}",
                metadata={
                    "clue_number": clue_num,
                    "direction": "down",
                    "puzzle_name": puzzle_name,
                    "puzzle_date": puzzle_date,
                    "answer_length": answer_length,
                },
            )
        )

    return samples


@task
def cryptic_crossword(benchmark_file: str | None = None) -> Task:
    """
    Evaluate a model's ability to solve cryptic crossword clues.

    Args:
        benchmark_file: Path to a specific benchmark JSON file. If None, loads all
                       benchmark files from the benchmark_data directory.

    Returns:
        An Inspect AI Task for evaluating cryptic crossword solving.
    """
    # Determine which files to load
    if benchmark_file:
        benchmark_files = [Path(benchmark_file)]
    else:
        benchmark_dir = PROJECT_ROOT / "data" / "benchmark"
        benchmark_files = list(benchmark_dir.glob("*.json"))

    # Load all samples
    all_samples = []
    for file in benchmark_files:
        samples = load_crossword_samples(file)
        all_samples.extend(samples)

    # Create the task with system message and solver
    return Task(
        dataset=all_samples,
        plan=[
            system_message(SYSTEM_PROMPT),
            generate(),
        ],
        scorer=cryptic_scorer(),
    )


if __name__ == "__main__":
    # Example usage
    logger.info("Cryptic Crossword Evaluation Task:")
    logger.info(
        "- cryptic_crossword: Evaluate on all crosswords "
        "(or specify benchmark_file for a single puzzle)"
    )
    logger.info("\nRun with: inspect eval eval/cryptic_crossword_eval.py")
