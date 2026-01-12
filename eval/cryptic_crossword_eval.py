"""Inspect AI evaluation for cryptic crossword solving."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import generate, system_message
from loguru import logger

# Get the project root directory (parent of the eval folder)
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from .env file
load_dotenv(PROJECT_ROOT / ".env")


def normalize_answer(answer: str) -> str:
    """Normalize an answer by converting to uppercase and removing spaces/punctuation."""
    return "".join(c for c in answer.upper() if c.isalnum())


@scorer(metrics=[accuracy(), stderr()])
def cryptic_scorer() -> Callable[[Any, Target], Score]:
    """Score cryptic crossword answers with exact match after normalization."""

    async def score(state: Any, target: Target) -> Score:
        # Get the model's answer
        model_answer = state.output.completion

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

    return score


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

        # Format the answer length hint
        length_hint = "-".join(str(n) for n in answer_length) + " letters"

        # Create the prompt
        prompt = f"""Solve this cryptic crossword clue:

Clue: {clue_text}
Answer length: {length_hint}

Provide only the answer word(s), with no explanation or additional text."""

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

        # Format the answer length hint
        length_hint = "-".join(str(n) for n in answer_length) + " letters"

        # Create the prompt
        prompt = f"""Solve this cryptic crossword clue:

Clue: {clue_text}
Answer length: {length_hint}

Provide only the answer word(s), with no explanation or additional text."""

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
            system_message(
                """You are an expert at solving cryptic crossword puzzles.
Cryptic crosswords contain clues that have both a definition and wordplay component.
Your task is to solve each clue and provide only the answer word(s).
Be concise - provide only the answer without explanation."""
            ),
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
