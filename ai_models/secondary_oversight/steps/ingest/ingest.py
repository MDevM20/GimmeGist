"""Ingest step: loads evaluation data for the secondary oversight model.

Since MedGemma is used as-is (no fine-tuning), the ingest step loads
evaluation data that pairs radiology reports with known missed findings.
"""

import logging

from steps.evaluate.dataset import load_evaluation_dataset

logger = logging.getLogger(__name__)


def ingest(
    source: str = "synthetic_demo",
    n_samples: int | None = None,
    rexerr_data_dir: str | None = None,
    image_dir: str | None = None,
    force_download: bool = False,
) -> list[dict]:
    """Load radiology report evaluation data.

    Args:
        source: Dataset source identifier ('synthetic_demo' or 'rexerr').
        n_samples: Optional limit on number of samples.
        rexerr_data_dir: Directory containing ReXErr-v1 CSVs.
        image_dir: Directory containing MIMIC-CXR images.
        force_download: If True, re-download even if cached.

    Returns:
        List of dicts with report_text, image_path, missed_findings,
        and original_report keys.
    """
    logger.info("Ingesting data from source=%s, n_samples=%s", source, n_samples)
    data = load_evaluation_dataset(
        source=source,
        split="test",
        n_samples=n_samples,
        rexerr_data_dir=rexerr_data_dir,
        image_dir=image_dir,
        force_download=force_download,
    )
    logger.info("Ingested %d samples", len(data))
    return data
