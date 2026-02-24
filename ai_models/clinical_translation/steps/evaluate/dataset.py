"""Dataset loader for clinical text simplification evaluation.

Supports loading the MedLane dataset (clinical ↔ simplified sentence pairs)
for evaluating how well the model translates clinical jargon to layman terms.

MedLane: https://github.com/machinelearning4health/MedLane
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Local cache directory
_CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "datasets"

# MedLane dataset URLs (raw GitHub)
_MEDLANE_BASE_URL = (
    "https://raw.githubusercontent.com/machinelearning4health/MedLane/main/data"
)
_MEDLANE_FILES = {
    "train": f"{_MEDLANE_BASE_URL}/train.json",
    "val": f"{_MEDLANE_BASE_URL}/val.json",
    "test": f"{_MEDLANE_BASE_URL}/test.json",
}


def _download_file(url: str, dest: Path) -> Path:
    """Download a file from a URL to a local destination."""
    import urllib.request

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        logger.info("Using cached file: %s", dest)
        return dest

    logger.info("Downloading %s → %s", url, dest)
    urllib.request.urlretrieve(url, dest)
    return dest


def _load_medlane_split(split: str) -> list[dict]:
    """Load a single MedLane split (train/val/test).

    Returns list of dicts with keys 'clinical' and 'simple'.
    """
    if split not in _MEDLANE_FILES:
        raise ValueError(
            f"Unknown split: {split}. Expected one of {list(_MEDLANE_FILES)}"
        )

    cache_path = _CACHE_DIR / "medlane" / f"{split}.json"
    _download_file(_MEDLANE_FILES[split], cache_path)

    with open(cache_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    # MedLane format: list of objects with 'src' (clinical) and 'tgt' (simple)
    pairs = []
    for item in raw_data:
        src = item.get("src") or item.get("source") or item.get("complex", "")
        tgt = item.get("tgt") or item.get("target") or item.get("simple", "")
        if src and tgt:
            pairs.append({"clinical": src.strip(), "simple": tgt.strip()})

    logger.info("Loaded %d pairs from MedLane %s split", len(pairs), split)
    return pairs


def load_evaluation_dataset(
    source: str = "medlane",
    split: str = "test",
    n_samples: int | None = None,
    force_download: bool = False,
) -> list[dict]:
    """Load evaluation dataset for clinical text simplification.

    Args:
        source: Dataset source identifier. Currently supports 'medlane'.
        split: Which split to load ('train', 'val', 'test').
        n_samples: If set, limit to this many samples.
        force_download: If True, re-download even if cached.

    Returns:
        List of dicts with 'clinical' and 'simple' keys.
    """
    if force_download:
        cache_dir = _CACHE_DIR / source
        if cache_dir.exists():
            import shutil

            shutil.rmtree(cache_dir)
            logger.info("Cleared cache for %s", source)

    if source == "medlane":
        data = _load_medlane_split(split)
    else:
        raise ValueError(f"Unknown dataset source: {source}. Supported: ['medlane']")

    if n_samples is not None and n_samples < len(data):
        data = data[:n_samples]
        logger.info("Limited dataset to %d samples", n_samples)

    return data
