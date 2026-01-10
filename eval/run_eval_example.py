"""Example script showing how to run the cryptic crossword evaluation programmatically."""

from inspect_ai import eval

from eval.cryptic_crossword_eval import cryptic_crossword


def main() -> None:
    """Run the cryptic crossword evaluation and print results."""
    # Run the evaluation
    print("Running cryptic crossword evaluation...")
    print("=" * 60)

    # Run with a mock model for testing (replace with real model in production)
    logs = eval(
        cryptic_crossword(),
        model="mockllm/model",
        limit=5,  # Only run 5 samples for this example
    )

    # Access the first log (there's only one task)
    log = logs[0]

    # Print summary results
    print("\nEvaluation Results:")
    print("=" * 60)
    print(f"Task: {log.eval.task}")
    print(f"Model: {log.eval.model}")
    print(f"Total samples: {log.samples}")
    print(f"Completed samples: {log.results.samples_completed}")

    # Print scores
    if log.results.scores:
        print("\nScores:")
        for score in log.results.scores:
            print(f"  {score.name}: {score.value:.3f}")

    # Print individual sample results
    print("\nSample Results:")
    print("-" * 60)
    for i, sample in enumerate(log.samples[:5], 1):  # Show first 5 samples
        print(f"\nSample {i}:")
        print(f"  Clue: {sample.input[:100]}...")  # First 100 chars of prompt
        print(f"  Expected: {sample.target}")
        if sample.scores:
            correct = sample.scores.get("cryptic_scorer", {}).get("value", False)
            print(f"  Correct: {correct}")

    print("\n" + "=" * 60)
    print(f"Evaluation log saved to: {log.location}")


if __name__ == "__main__":
    main()
