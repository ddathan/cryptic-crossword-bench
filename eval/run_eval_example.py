"""Example script showing how to run the cryptic crossword evaluation programmatically."""

from inspect_ai import eval
from loguru import logger

from eval.cryptic_crossword_eval import cryptic_crossword


def main() -> None:
    """Run the cryptic crossword evaluation and print results."""
    # Run the evaluation
    logger.info("Running cryptic crossword evaluation...")
    logger.info("=" * 60)

    # Run with a mock model for testing (replace with real model in production)
    logs = eval(
        cryptic_crossword(),
        model="mockllm/model",
        limit=5,  # Only run 5 samples for this example
    )

    # Access the first log (there's only one task)
    log = logs[0]

    # Print summary results
    logger.info("\nEvaluation Results:")
    logger.info("=" * 60)
    logger.info(f"Task: {log.eval.task}")
    logger.info(f"Model: {log.eval.model}")
    logger.info(f"Total samples: {log.samples}")
    logger.info(f"Completed samples: {log.results.completed_samples}")

    # Print scores
    if log.results.scores:
        logger.info("\nScores:")
        for score in log.results.scores:
            logger.info(f"  {score.name}: {score.value:.3f}")

    # Print individual sample results
    logger.info("\nSample Results:")
    logger.info("-" * 60)
    for i, sample in enumerate(log.samples[:5], 1):  # Show first 5 samples
        logger.info(f"\nSample {i}:")
        logger.info(f"  Clue: {sample.input[:100]}...")  # First 100 chars of prompt
        logger.info(f"  Expected: {sample.target}")
        if sample.scores:
            correct = sample.scores.get("cryptic_scorer", {}).get("value", False)
            logger.info(f"  Correct: {correct}")

    logger.info("\n" + "=" * 60)
    logger.info(f"Evaluation log saved to: {log.location}")


if __name__ == "__main__":
    main()
