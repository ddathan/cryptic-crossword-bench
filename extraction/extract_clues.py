"""Extract clues from crossword PDF files using layout analysis."""

import json
import re
from pathlib import Path
from typing import Any

import pdfplumber


def parse_answer_length(length_str: str) -> list[int]:
    """Parse answer length from format like '(8)' or '(4,4)' or '(4,3,5)'."""
    length_str = length_str.strip("()")
    if "," in length_str:
        return [int(x.strip()) for x in length_str.split(",")]
    return [int(length_str)]


def extract_clues_from_pdf(pdf_path: Path) -> dict[str, Any]:
    """Extract clues from a PDF file using layout analysis."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]

        # Get page dimensions to determine column boundary
        page_width = page.width
        middle_x = page_width / 2

        # Extract words with their positions
        words = page.extract_words()

        # Find metadata
        text = page.extract_text()
        lines = text.split("\n")
        metadata = {}
        for line in lines[:5]:
            if "20" in line and any(
                month in line
                for month in [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ]
            ):
                metadata["date"] = line.strip()
            elif "Times" in line or "Cryptic" in line or "Quick" in line:
                metadata["puzzle_name"] = line.strip()

        # Separate words into left (ACROSS) and right (DOWN) columns
        left_words = [w for w in words if w["x0"] < middle_x]
        right_words = [w for w in words if w["x0"] >= middle_x]

        # Reconstruct text for each column
        def reconstruct_text(words_list: list[dict[str, Any]]) -> str:
            """Reconstruct text from words, grouped by lines."""
            if not words_list:
                return ""

            # Group words by their y-position (with some tolerance for same line)
            lines_dict: dict[float, list[dict[str, Any]]] = {}
            for word in words_list:
                y = round(word["top"], 1)  # Round to group nearby words
                if y not in lines_dict:
                    lines_dict[y] = []
                lines_dict[y].append(word)

            # Sort by y-position and reconstruct lines
            sorted_ys = sorted(lines_dict.keys())
            text_lines = []
            for y in sorted_ys:
                line_words = sorted(lines_dict[y], key=lambda w: w["x0"])
                line_text = " ".join(w["text"] for w in line_words)
                text_lines.append(line_text)

            return "\n".join(text_lines)

        across_text = reconstruct_text(left_words)
        down_text = reconstruct_text(right_words)

        # Extract clues from each section
        pattern = r"(\d+)\s+(.+?)\s+(\(\d+(?:,\s*\d+)*\))"

        across_clues = {}
        for match in re.finditer(pattern, across_text):
            clue_num = int(match.group(1))
            across_clues[clue_num] = {
                "clue": match.group(2).strip(),
                "answer_length": parse_answer_length(match.group(3)),
                "answer": None,
            }

        down_clues = {}
        for match in re.finditer(pattern, down_text):
            clue_num = int(match.group(1))
            down_clues[clue_num] = {
                "clue": match.group(2).strip(),
                "answer_length": parse_answer_length(match.group(3)),
                "answer": None,
            }

    return {
        "metadata": metadata,
        "across": across_clues,
        "down": down_clues,
    }


def main() -> None:
    """Extract clues from all crossword PDFs."""
    data_dir = Path("data/raw")
    output_dir = Path("data/extracted")
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in data_dir.glob("*.pdf"):
        print(f"Processing {pdf_path.name}...")

        try:
            clues_data = extract_clues_from_pdf(pdf_path)

            output_path = output_dir / f"{pdf_path.stem}_clues.json"
            with open(output_path, "w") as f:
                json.dump(clues_data, f, indent=2)

            print(f"  Extracted {len(clues_data['across'])} across clues")
            print(f"  Extracted {len(clues_data['down'])} down clues")
            print(f"  Saved to {output_path}")
        except Exception as e:
            print(f"  Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
