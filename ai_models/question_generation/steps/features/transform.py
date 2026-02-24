"""Features step: pass-through for the question generation model.

No feature engineering is needed for a prompt-based LLM model.
The raw medical text is passed directly to the LangGraph nodes.
"""

import logging

logger = logging.getLogger(__name__)


def transform():
    """Return None — no feature transformation needed.

    The question generation model uses raw text input directly.
    This step exists for pipeline structure consistency.
    """
    logger.info("Transform step: pass-through (no feature engineering for LLM model)")
    return None
