"""Prompts for the cryptic crossword evaluation."""

SYSTEM_PROMPT = """\
You are an expert at solving cryptic crossword puzzles.

You may think through the clue step by step, but you MUST provide your final answer
wrapped in <answer></answer> tags. For example: <answer>EXAMPLE</answer>
"""

CLUE_PROMPT_TEMPLATE = """\
Solve this cryptic crossword clue:

Clue: {clue_text}
Answer length: {length_hint}

Think through the clue carefully and then provide your final answer
wrapped in <answer></answer> tags.
"""


def format_clue_prompt(clue_text: str, answer_length: list[int]) -> str:
    """Format a clue into a prompt for the model.

    Args:
        clue_text: The cryptic crossword clue text
        answer_length: List of integers representing word lengths (e.g., [4, 5] for "4-5 letters")

    Returns:
        Formatted prompt string
    """
    length_hint = "-".join(str(n) for n in answer_length) + " letters"
    return CLUE_PROMPT_TEMPLATE.format(clue_text=clue_text, length_hint=length_hint)
