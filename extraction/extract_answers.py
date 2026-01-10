"""Extract answers from completed crossword images using Claude API."""

import base64
import json
import os
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def encode_image(image_path: Path) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.standard_b64encode(image_file.read()).decode("utf-8")


def get_image_media_type(image_path: Path) -> str:
    """Get the media type for the image."""
    suffix = image_path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    elif suffix in [".jpg", ".jpeg"]:
        return "image/jpeg"
    elif suffix == ".gif":
        return "image/gif"
    elif suffix == ".webp":
        return "image/webp"
    else:
        raise ValueError(f"Unsupported image format: {suffix}")


def extract_answers_with_claude(image_path: Path, clues_data: dict[str, Any]) -> dict[str, Any]:
    """Use Claude API to extract answers from crossword image."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set.\n"
            "Please set it by running: export ANTHROPIC_API_KEY='your-api-key'\n"
            "You can get your API key from: https://console.anthropic.com/settings/keys"
        )

    client = anthropic.Anthropic(api_key=api_key)

    # Encode image
    image_data = encode_image(image_path)
    media_type = get_image_media_type(image_path)

    # Create prompt with clue information
    across_clues = clues_data.get("across", {})
    down_clues = clues_data.get("down", {})

    across_nums = ", ".join(str(n) for n in sorted(across_clues.keys()))
    down_nums = ", ".join(str(n) for n in sorted(down_clues.keys()))

    prompt = f"""This is a completed cryptic crossword puzzle grid.
Please extract all the answers from the grid.

The puzzle has:
- {len(across_clues)} ACROSS clues (numbers: {across_nums})
- {len(down_clues)} DOWN clues (numbers: {down_nums})

Please analyze the grid carefully and provide the answers in JSON format:
{{
  "across": {{
    "1": "ANSWER",
    "5": "ANSWER",
    ...
  }},
  "down": {{
    "1": "ANSWER",
    "2": "ANSWER",
    ...
  }}
}}

Important:
- Read each answer carefully from left to right (for ACROSS) and top to bottom (for DOWN)
- The numbered cells indicate where each answer starts
- Multi-word answers should be written as single words without spaces
  (e.g., "RIOBRAVO" not "RIO BRAVO")
- Only include letters, no spaces or punctuation
- Make sure to include ALL answers for all clue numbers listed above"""

    # Call Claude API
    message = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {  # type: ignore[list-item]
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    # Extract response
    first_block = message.content[0]
    if not hasattr(first_block, "text"):
        raise ValueError(f"Unexpected response type: {type(first_block)}")
    response_text: str = first_block.text

    # Try to extract JSON from response
    # Look for JSON block in response
    json_match = response_text
    if "```json" in response_text:
        json_match = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        json_match = response_text.split("```")[1].split("```")[0].strip()

    # Parse JSON
    try:
        answers: dict[str, Any] = json.loads(json_match)
        return answers
    except json.JSONDecodeError:
        print(f"Failed to parse JSON from response:\n{response_text}")
        raise


def combine_clues_and_answers(
    clues_data: dict[str, Any], answers_data: dict[str, Any]
) -> dict[str, Any]:
    """Combine clues and answers into a single structure."""
    result = {
        "metadata": clues_data.get("metadata", {}),
        "across": {},
        "down": {},
    }

    # Add ACROSS
    for num_str, clue_info in clues_data.get("across", {}).items():
        result["across"][num_str] = {
            "clue": clue_info["clue"],
            "answer_length": clue_info["answer_length"],
            "answer": answers_data.get("across", {}).get(str(num_str)),
        }

    # Add DOWN
    for num_str, clue_info in clues_data.get("down", {}).items():
        result["down"][num_str] = {
            "clue": clue_info["clue"],
            "answer_length": clue_info["answer_length"],
            "answer": answers_data.get("down", {}).get(str(num_str)),
        }

    return result


def main() -> None:
    """Extract answers from all completed crossword images."""
    data_dir = Path("data/raw")
    extracted_dir = Path("data/extracted")
    output_dir = Path("data/benchmark")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each completed crossword image
    for png_path in data_dir.glob("*-complete.png"):
        print(f"\nProcessing {png_path.name}...")

        # Find corresponding clues file
        # Remove "-complete" from the filename
        base_name = png_path.stem.replace("-complete", "")
        clues_path = extracted_dir / f"{base_name}_clues.json"

        if not clues_path.exists():
            print(f"  Warning: Clues file not found at {clues_path}")
            continue

        # Load clues
        with open(clues_path) as f:
            clues_data = json.load(f)

        across_count = len(clues_data["across"])
        down_count = len(clues_data["down"])
        print(f"  Loaded {across_count} across and {down_count} down clues")

        # Extract answers using Claude
        print("  Extracting answers with Claude API...")
        answers_data = extract_answers_with_claude(png_path, clues_data)

        print(f"  Extracted {len(answers_data.get('across', {}))} across answers")
        print(f"  Extracted {len(answers_data.get('down', {}))} down answers")

        # Combine clues and answers
        complete_data = combine_clues_and_answers(clues_data, answers_data)

        # Save complete data
        output_path = output_dir / f"{base_name}_complete.json"
        with open(output_path, "w") as f:
            json.dump(complete_data, f, indent=2)

        print(f"  Saved complete data to {output_path}")


if __name__ == "__main__":
    main()
