"""Dataset loader for question generation evaluation.

Supports loading the MedQuAD dataset (medical Q&A pairs from NIH)
for evaluating how well the model generates grounded patient questions.

MedQuAD: https://huggingface.co/datasets/keivalya/MedQuad-MedicalQnADataset
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Local cache directory
_CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "datasets"


def _load_medquad(n_samples: int | None = None) -> list[dict]:
    """Load MedQuAD dataset from HuggingFace.

    Returns list of dicts with keys 'clinical_text' and 'reference_question'.
    The 'Answer' field (clinical text) serves as model input, and the
    'Question' field provides reference questions for evaluation.
    """
    cache_path = _CACHE_DIR / "medquad" / "medquad.json"

    if cache_path.exists():
        logger.info("Using cached MedQuAD data: %s", cache_path)
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        logger.info("Downloading MedQuAD from HuggingFace...")
        try:
            from datasets import load_dataset

            ds = load_dataset(
                "keivalya/MedQuad-MedicalQnADataset",
                split="train",
            )
        except Exception as e:
            logger.error("Failed to download MedQuAD: %s", e)
            raise

        # Convert to our format
        data = []
        for item in ds:
            answer = (item.get("Answer") or "").strip()
            question = (item.get("Question") or "").strip()
            if answer and question:
                data.append(
                    {
                        "clinical_text": answer,
                        "reference_question": question,
                    }
                )

        # Cache locally
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Cached %d MedQuAD pairs to %s", len(data), cache_path)

    logger.info("Loaded %d pairs from MedQuAD", len(data))

    if n_samples is not None and n_samples < len(data):
        data = data[:n_samples]
        logger.info("Limited dataset to %d samples", n_samples)

    return data


def load_evaluation_dataset(
    source: str = "medquad",
    n_samples: int | None = None,
    force_download: bool = False,
) -> list[dict]:
    """Load evaluation dataset for question generation.

    Args:
        source: Dataset source identifier. Currently supports 'medquad'.
        n_samples: If set, limit to this many samples.
        force_download: If True, re-download even if cached.

    Returns:
        List of dicts with 'clinical_text' and 'reference_question' keys.
    """
    if force_download:
        cache_dir = _CACHE_DIR / source
        if cache_dir.exists():
            import shutil

            shutil.rmtree(cache_dir)
            logger.info("Cleared cache for %s", source)

    if source == "medquad":
        return _load_medquad(n_samples=n_samples)
    else:
        raise ValueError(f"Unknown dataset source: {source}. Supported: ['medquad']")
