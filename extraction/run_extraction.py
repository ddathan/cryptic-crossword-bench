"""Main script to extract complete crossword data from PDFs and images."""

import json
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

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

    logger.info("=" * 70)
    logger.info("Cryptic Crossword Extraction Pipeline")
    logger.info("=" * 70)

    # Step 1: Extract clues from PDFs
    logger.info("\nStep 1: Extracting clues from PDFs...")
    logger.info("-" * 70)

    pdf_files = list(data_dir.glob("*.pdf"))
    for pdf_path in pdf_files:
        logger.info(f"\nProcessing {pdf_path.name}...")

        try:
            clues_data = extract_clues_from_pdf(pdf_path)

            output_path = extracted_dir / f"{pdf_path.stem}_clues.json"
            with open(output_path, "w") as f:
                json.dump(clues_data, f, indent=2)

            logger.info(f"  ✓ Extracted {len(clues_data['across'])} across clues")
            logger.info(f"  ✓ Extracted {len(clues_data['down'])} down clues")
            logger.info(f"  ✓ Saved to {output_path}")
        except Exception as e:
            logger.error(f"  ✗ Error: {e}")

    # Step 2: Extract answers from images using Claude
    logger.info("\n\nStep 2: Extracting answers from images using Claude API...")
    logger.info("-" * 70)

    for png_path in data_dir.glob("*-complete.png"):
        logger.info(f"\nProcessing {png_path.name}...")

        # Find corresponding clues file
        base_name = png_path.stem.replace("-complete", "")
        clues_path = extracted_dir / f"{base_name}_clues.json"

        if not clues_path.exists():
            logger.warning(f"  ✗ Warning: Clues file not found at {clues_path}")
            continue

        # Load clues
        with open(clues_path) as f:
            clues_data = json.load(f)

        logger.info(
            f"  → Loaded {len(clues_data['across'])} across and "
            f"{len(clues_data['down'])} down clues"
        )

        try:
            # Extract answers using Claude
            logger.info("  → Analyzing image with Claude API...")
            answers_data = extract_answers_with_claude(png_path, clues_data)

            logger.info(f"  ✓ Extracted {len(answers_data.get('across', {}))} across answers")
            logger.info(f"  ✓ Extracted {len(answers_data.get('down', {}))} down answers")

            # Combine clues and answers
            complete_data = combine_clues_and_answers(clues_data, answers_data)

            # Save complete data
            output_path = output_dir / f"{base_name}.json"
            with open(output_path, "w") as f:
                json.dump(complete_data, f, indent=2)

            logger.info(f"  ✓ Saved complete benchmark data to {output_path}")

        except Exception as e:
            logger.error(f"  ✗ Error: {e}")
            if "credit balance" in str(e).lower():
                logger.warning("\n  ⚠ Please add credits to your Anthropic account:")
                logger.warning("    https://console.anthropic.com/settings/billing")
                return

    # Step 3: Generate summary
    logger.info("\n\n" + "=" * 70)
    logger.info("Extraction Complete!")
    logger.info("=" * 70)

    benchmark_files = list(output_dir.glob("*.json"))
    if benchmark_files:
        logger.info(f"\nGenerated {len(benchmark_files)} benchmark file(s):")
        for benchmark_path in benchmark_files:
            with open(benchmark_path) as benchmark_file:
                data = json.load(benchmark_file)
                total_clues = len(data.get("across", {})) + len(data.get("down", {}))
                logger.info(f"  • {benchmark_path.name}: {total_clues} total clues")

        logger.info(f"\nBenchmark data saved to: {output_dir}/")
    else:
        logger.info("\nNo benchmark files were generated.")
        logger.info("Please check the errors above and try again.")


if __name__ == "__main__":
    main()
