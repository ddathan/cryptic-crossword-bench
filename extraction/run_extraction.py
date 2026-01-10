"""Main script to extract complete crossword data from PDFs and images."""

import json
from pathlib import Path

from dotenv import load_dotenv

from extraction.extract_answers import combine_clues_and_answers, extract_answers_with_claude
from extraction.extract_clues import extract_clues_from_pdf

# Load environment variables
load_dotenv()


def main() -> None:
    """Extract complete crossword data from PDFs and images."""
    data_dir = Path("data/raw")
    extracted_dir = Path("data/extracted")
    output_dir = Path("data/benchmark")

    # Create output directories
    extracted_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Cryptic Crossword Extraction Pipeline")
    print("=" * 70)

    # Step 1: Extract clues from PDFs
    print("\nStep 1: Extracting clues from PDFs...")
    print("-" * 70)

    pdf_files = list(data_dir.glob("*.pdf"))
    for pdf_path in pdf_files:
        print(f"\nProcessing {pdf_path.name}...")

        try:
            clues_data = extract_clues_from_pdf(pdf_path)

            output_path = extracted_dir / f"{pdf_path.stem}_clues.json"
            with open(output_path, "w") as f:
                json.dump(clues_data, f, indent=2)

            print(f"  ✓ Extracted {len(clues_data['across'])} across clues")
            print(f"  ✓ Extracted {len(clues_data['down'])} down clues")
            print(f"  ✓ Saved to {output_path}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Step 2: Extract answers from images using Claude
    print("\n\nStep 2: Extracting answers from images using Claude API...")
    print("-" * 70)

    for png_path in data_dir.glob("*-complete.png"):
        print(f"\nProcessing {png_path.name}...")

        # Find corresponding clues file
        base_name = png_path.stem.replace("-complete", "")
        clues_path = extracted_dir / f"{base_name}_clues.json"

        if not clues_path.exists():
            print(f"  ✗ Warning: Clues file not found at {clues_path}")
            continue

        # Load clues
        with open(clues_path) as f:
            clues_data = json.load(f)

        print(
            f"  → Loaded {len(clues_data['across'])} across and "
            f"{len(clues_data['down'])} down clues"
        )

        try:
            # Extract answers using Claude
            print("  → Analyzing image with Claude API...")
            answers_data = extract_answers_with_claude(png_path, clues_data)

            print(f"  ✓ Extracted {len(answers_data.get('across', {}))} across answers")
            print(f"  ✓ Extracted {len(answers_data.get('down', {}))} down answers")

            # Combine clues and answers
            complete_data = combine_clues_and_answers(clues_data, answers_data)

            # Save complete data
            output_path = output_dir / f"{base_name}.json"
            with open(output_path, "w") as f:
                json.dump(complete_data, f, indent=2)

            print(f"  ✓ Saved complete benchmark data to {output_path}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            if "credit balance" in str(e).lower():
                print("\n  ⚠ Please add credits to your Anthropic account:")
                print("    https://console.anthropic.com/settings/billing")
                return

    # Step 3: Generate summary
    print("\n\n" + "=" * 70)
    print("Extraction Complete!")
    print("=" * 70)

    benchmark_files = list(output_dir.glob("*.json"))
    if benchmark_files:
        print(f"\nGenerated {len(benchmark_files)} benchmark file(s):")
        for benchmark_path in benchmark_files:
            with open(benchmark_path) as benchmark_file:
                data = json.load(benchmark_file)
                total_clues = len(data.get("across", {})) + len(data.get("down", {}))
                print(f"  • {benchmark_path.name}: {total_clues} total clues")

        print(f"\nBenchmark data saved to: {output_dir}/")
    else:
        print("\nNo benchmark files were generated.")
        print("Please check the errors above and try again.")


if __name__ == "__main__":
    main()
