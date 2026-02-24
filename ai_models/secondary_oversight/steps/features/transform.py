"""Features step: pass-through for the secondary oversight model.

No feature engineering is needed for a prompt-based multimodal LLM model.
The raw report text and image path are passed directly to the LangGraph nodes.
"""

import logging

logger = logging.getLogger(__name__)


def transform():
    """Return None — no feature transformation needed.

    The secondary oversight model uses raw text and images directly.
    This step exists for pipeline structure consistency.
    """
    logger.info("Transform step: pass-through (no feature engineering for LLM model)")
    return None
