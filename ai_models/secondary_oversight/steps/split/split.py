"""Split step: creates train/test indexes for evaluation.

For the secondary oversight model (no fine-tuning), this simply returns
the full dataset as the test split for evaluation purposes.
"""

import logging

logger = logging.getLogger(__name__)


def split(data: list[dict], test_ratio: float = 1.0) -> dict[str, list[int]]:
    """Create split indexes for the evaluation data.

    Args:
        data: The full dataset (list of dicts).
        test_ratio: Fraction of data to use for testing (default 1.0 = all).

    Returns:
        Dict with 'train' and 'test' keys containing index lists.
    """
    n = len(data)
    n_test = int(n * test_ratio)

    test_idx = list(range(n_test))
    train_idx = list(range(n_test, n))

    logger.info("Split: %d train, %d test (total=%d)", len(train_idx), len(test_idx), n)

    return {
        "train": train_idx,
        "test": test_idx,
    }
