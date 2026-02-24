"""Dataset loader for secondary oversight evaluation.

Supports two data sources:
1. ReXErr-v1 (PhysioNet) — chest X-ray reports with injected errors.
   Requires manual download of CSVs from PhysioNet.
2. Synthetic demo — hardcoded examples for testing without PhysioNet access.

Each sample returns:
    {
        "report_text": str,        # The (possibly erroneous) radiology report
        "image_path": str | None,  # Path to the chest X-ray image (if available)
        "missed_findings": list[str],  # Ground-truth missed/erroneous findings
        "original_report": str,    # The correct, original report
    }
"""

import json
import logging
import os
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Local cache directory
_CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "datasets"


# ---------------------------------------------------------------------------
# Synthetic demo dataset
# ---------------------------------------------------------------------------

_SYNTHETIC_DEMO: list[dict] = [
    {
        "report_text": (
            "PA and lateral chest radiograph. The heart is normal in size. "
            "The lungs are clear bilaterally. No pleural effusion. "
            "No pneumothorax. The mediastinal contours are normal."
        ),
        "original_report": (
            "PA and lateral chest radiograph. The heart is normal in size. "
            "The lungs are clear bilaterally. No pleural effusion. "
            "No pneumothorax. The mediastinal contours are normal. "
            "Mild degenerative changes of the thoracic spine are noted. "
            "There is mild osteopenia."
        ),
        "missed_findings": [
            "Mild degenerative changes of the thoracic spine",
            "Mild osteopenia",
        ],
        "image_path": None,
    },
    {
        "report_text": (
            "Single frontal view of the chest. The cardiac silhouette is "
            "mildly enlarged. Mild pulmonary vascular congestion. "
            "No focal consolidation."
        ),
        "original_report": (
            "Single frontal view of the chest. The cardiac silhouette is "
            "mildly enlarged. Mild pulmonary vascular congestion. "
            "No focal consolidation. Small bilateral pleural effusions "
            "are present. A 6mm pulmonary nodule is seen in the right "
            "lower lobe."
        ),
        "missed_findings": [
            "Small bilateral pleural effusions",
            "6mm pulmonary nodule in the right lower lobe",
        ],
        "image_path": None,
    },
    {
        "report_text": (
            "Chest radiograph, two views. The lungs are hyperinflated "
            "consistent with COPD. Flattening of the diaphragms. "
            "No acute infiltrate."
        ),
        "original_report": (
            "Chest radiograph, two views. The lungs are hyperinflated "
            "consistent with COPD. Flattening of the diaphragms. "
            "No acute infiltrate. There is a small right apical "
            "pneumothorax. Subcutaneous emphysema in the right "
            "chest wall."
        ),
        "missed_findings": [
            "Small right apical pneumothorax",
            "Subcutaneous emphysema in the right chest wall",
        ],
        "image_path": None,
    },
    {
        "report_text": (
            "PA chest radiograph. There is a left lower lobe opacity "
            "consistent with pneumonia. The heart size is normal. "
            "No pneumothorax."
        ),
        "original_report": (
            "PA chest radiograph. There is a left lower lobe opacity "
            "consistent with pneumonia. The heart size is normal. "
            "No pneumothorax. There is a widened mediastinum. "
            "Aortic calcifications are noted."
        ),
        "missed_findings": [
            "Widened mediastinum",
            "Aortic calcifications",
        ],
        "image_path": None,
    },
    {
        "report_text": (
            "Portable AP chest radiograph. Endotracheal tube in "
            "satisfactory position. The heart is at the upper limits "
            "of normal size. Bilateral basilar atelectasis."
        ),
        "original_report": (
            "Portable AP chest radiograph. Endotracheal tube in "
            "satisfactory position. The heart is at the upper limits "
            "of normal size. Bilateral basilar atelectasis. "
            "Right internal jugular central venous catheter tip is in "
            "the superior vena cava. Nasogastric tube tip is in the "
            "stomach. A right-sided chest tube is present."
        ),
        "missed_findings": [
            "Right internal jugular central venous catheter tip in the SVC",
            "Nasogastric tube tip in the stomach",
            "Right-sided chest tube",
        ],
        "image_path": None,
    },
    {
        "report_text": (
            "Frontal and lateral chest radiograph. Normal cardiac "
            "silhouette. Clear lungs. No pleural abnormality."
        ),
        "original_report": (
            "Frontal and lateral chest radiograph. Normal cardiac "
            "silhouette. Clear lungs. No pleural abnormality. "
            "Compression fracture of T12 vertebral body with "
            "approximately 30% height loss. Surgical clips in the "
            "right upper quadrant."
        ),
        "missed_findings": [
            "Compression fracture of T12 with 30% height loss",
            "Surgical clips in the right upper quadrant",
        ],
        "image_path": None,
    },
    {
        "report_text": (
            "Two-view chest. Stable cardiomegaly. Bilateral pleural "
            "effusions, left greater than right. Bibasilar "
            "atelectasis versus consolidation."
        ),
        "original_report": (
            "Two-view chest. Stable cardiomegaly. Bilateral pleural "
            "effusions, left greater than right. Bibasilar "
            "atelectasis versus consolidation. Calcified granuloma "
            "in the right upper lobe. Hilar lymphadenopathy cannot "
            "be excluded."
        ),
        "missed_findings": [
            "Calcified granuloma in the right upper lobe",
            "Hilar lymphadenopathy cannot be excluded",
        ],
        "image_path": None,
    },
    {
        "report_text": (
            "Chest PA and lateral. The lungs are clear. No focal "
            "consolidation, pleural effusion, or pneumothorax. "
            "Normal heart size."
        ),
        "original_report": (
            "Chest PA and lateral. The lungs are clear. No focal "
            "consolidation, pleural effusion, or pneumothorax. "
            "Normal heart size. There is a tortuous aorta. "
            "Moderate diffuse osteopenia of the visualized bony "
            "structures consistent with osteoporosis."
        ),
        "missed_findings": [
            "Tortuous aorta",
            "Moderate diffuse osteopenia consistent with osteoporosis",
        ],
        "image_path": None,
    },
    {
        "report_text": (
            "AP portable chest. Limited study due to patient rotation. "
            "The cardiac silhouette appears enlarged. Pulmonary "
            "vascularity is within normal limits."
        ),
        "original_report": (
            "AP portable chest. Limited study due to patient rotation. "
            "The cardiac silhouette appears enlarged. Pulmonary "
            "vascularity is within normal limits. There is a left "
            "lower lobe retrocardiac opacity suggestive of atelectasis "
            "or early pneumonia. Elevation of the left hemidiaphragm."
        ),
        "missed_findings": [
            "Left lower lobe retrocardiac opacity (atelectasis or early pneumonia)",
            "Elevation of the left hemidiaphragm",
        ],
        "image_path": None,
    },
    {
        "report_text": (
            "Chest radiograph, PA view. Lungs are clear bilaterally. "
            "No consolidation or effusion. The cardiomediastinal "
            "silhouette is unremarkable."
        ),
        "original_report": (
            "Chest radiograph, PA view. Lungs are clear bilaterally. "
            "No consolidation or effusion. The cardiomediastinal "
            "silhouette is unremarkable. There is a 1.2 cm calcified "
            "lymph node in the right hilum. Cervical rib on the left "
            "side is an incidental finding."
        ),
        "missed_findings": [
            "1.2 cm calcified lymph node in the right hilum",
            "Cervical rib on the left side (incidental)",
        ],
        "image_path": None,
    },
]


# ---------------------------------------------------------------------------
# ReXErr-v1 loader
# ---------------------------------------------------------------------------


def _load_rexerr_split(
    data_dir: str | Path,
    split: str = "test",
    image_dir: str | Path | None = None,
) -> list[dict]:
    """Load a ReXErr-v1 split from user-provided CSVs.

    Expected CSV columns:
        - dicom_id, study_id, subject_id
        - original_report
        - error_report
        - errors_sampled  (JSON string of error descriptions)

    Args:
        data_dir: Directory containing ReXErr CSVs.
        split: One of 'train', 'val', 'test'.
        image_dir: Optional directory containing MIMIC-CXR images.

    Returns:
        List of sample dicts.
    """
    data_dir = Path(data_dir)
    csv_path = data_dir / f"ReXErr-report-level_{split}.csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"ReXErr-v1 CSV not found: {csv_path}. "
            "Download from PhysioNet (https://physionet.org/content/rexerr-v1/) "
            "and place the CSVs in the configured REXERR_DATA_DIR."
        )

    df = pd.read_csv(csv_path)
    logger.info("Loaded %d rows from %s", len(df), csv_path)

    samples = []
    for _, row in df.iterrows():
        # Parse the errors_sampled column (JSON string → list)
        try:
            errors = json.loads(row.get("errors_sampled", "[]"))
            if isinstance(errors, str):
                errors = [errors]
        except (json.JSONDecodeError, TypeError):
            errors = [str(row.get("errors_sampled", ""))]

        # Try to find the corresponding image
        image_path = None
        if image_dir:
            img_dir = Path(image_dir)
            dicom_id = row.get("dicom_id", "")
            subject_id = str(row.get("subject_id", ""))
            study_id = str(row.get("study_id", ""))

            # MIMIC-CXR image path pattern
            candidate = (
                img_dir
                / f"p{subject_id[:2]}"
                / f"p{subject_id}"
                / f"s{study_id}"
                / f"{dicom_id}.jpg"
            )
            if candidate.exists():
                image_path = str(candidate)

        samples.append(
            {
                "report_text": str(row.get("error_report", "")),
                "original_report": str(row.get("original_report", "")),
                "missed_findings": errors,
                "image_path": image_path,
            }
        )

    logger.info("Parsed %d ReXErr-v1 samples (split=%s)", len(samples), split)
    return samples


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_evaluation_dataset(
    source: str = "synthetic_demo",
    split: str = "test",
    n_samples: int | None = None,
    rexerr_data_dir: str | None = None,
    image_dir: str | None = None,
    force_download: bool = False,
) -> list[dict]:
    """Load evaluation dataset for secondary oversight.

    Args:
        source: Dataset source — 'synthetic_demo' or 'rexerr'.
        split: Which split to load ('train', 'val', 'test').
        n_samples: If set, limit to this many samples.
        rexerr_data_dir: Directory containing ReXErr-v1 CSVs.
        image_dir: Directory containing MIMIC-CXR images.
        force_download: Not used for local datasets; kept for API compatibility.

    Returns:
        List of dicts with keys: report_text, image_path,
        missed_findings, original_report.
    """
    if source == "synthetic_demo":
        data = list(_SYNTHETIC_DEMO)
        logger.info("Loaded %d synthetic demo samples", len(data))
    elif source == "rexerr":
        if not rexerr_data_dir:
            rexerr_data_dir = str(_CACHE_DIR / "rexerr")
        data = _load_rexerr_split(rexerr_data_dir, split, image_dir)
    else:
        raise ValueError(
            f"Unknown dataset source: {source}. "
            "Supported: ['synthetic_demo', 'rexerr']"
        )

    if n_samples is not None and n_samples < len(data):
        data = data[:n_samples]
        logger.info("Limited dataset to %d samples", n_samples)

    return data
