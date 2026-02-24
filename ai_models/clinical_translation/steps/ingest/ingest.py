"""Ingest step: loads evaluation data for the clinical translation model.

Since MedGemma is used as-is (no fine-tuning), the ingest step loads the
MedLane evaluation dataset as the primary data source.
"""

import logging

from steps.evaluate.dataset import load_evaluation_dataset

logger = logging.getLogger(__name__)


def ingest(
    source: str = "medlane",
    n_samples: int | None = None,
    force_download: bool = False,
) -> list[dict]:
    """Load clinical text evaluation data.

    Args:
        source: Dataset source identifier.
        n_samples: Optional limit on number of samples.
        force_download: If True, re-download even if cached.

    Returns:
        List of dicts with 'clinical' and 'simple' keys.
    """
    logger.info("Ingesting data from source=%s, n_samples=%s", source, n_samples)
    data = load_evaluation_dataset(
        source=source,
        split="test",
        n_samples=n_samples,
        force_download=force_download,
    )
    logger.info("Ingested %d samples", len(data))
    return data
