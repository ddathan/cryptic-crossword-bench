"""Prompts for the cryptic crossword evaluation."""

SYSTEM_PROMPT = """\
You are an expert at solving cryptic crossword puzzles.

Cryptic crosswords contain clues that have both a definition and wordplay component.
The definition is typically at the beginning or end of the clue, while the wordplay
provides an alternative way to derive the answer through techniques like anagrams,
hidden words, double meanings, homophones, containers, and more.

Your task is to solve each clue by:
1. Identifying the definition part of the clue
2. Working out the wordplay
3. Finding the answer that satisfies both

You may think through the clue step by step, but you MUST provide your final answer
wrapped in <answer></answer> tags. For example: <answer>EXAMPLE</answer>
"""

CLUE_PROMPT_TEMPLATE = """\
Solve this cryptic crossword clue:

Clue: {clue_text}
Answer length: {length_hint}

Think through the clue carefully, identifying the definition and wordplay components.
Then provide your final answer wrapped in <answer></answer> tags.
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
