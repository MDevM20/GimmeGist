"""LangGraph node implementations for secondary oversight.

Each node calls MedGemma via ChatGoogleGenerativeAI to process one
stage of the secondary diagnostic oversight pipeline:
    1. parse_imaging   — extract all visible findings (multimodal)
    2. identify_findings — compare against the report to find gaps
    3. generate_questions — turn gaps into gentle patient questions

LLM instances are lazily created at invocation time so the graph can
be compiled without an API key (required for MLflow logging).
"""

import base64
import logging
import mimetypes
from pathlib import Path
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage

from steps.model.prompts import (
    GENERATE_QUESTIONS_PROMPT,
    IDENTIFY_FINDINGS_PROMPT,
    PARSE_IMAGING_PROMPT,
    SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class SecondaryOversightState(TypedDict):
    """State schema for the secondary oversight graph."""

    report_text: str
    image_path: str  # may be empty string if no image available
    parsed_findings: str
    missed_findings: str
    patient_questions: str


def _create_llm(model_name: str, temperature: float):
    """Create a ChatGoogleGenerativeAI instance (lazy, at call time)."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
    )


def _build_image_content(image_path: str) -> dict | None:
    """Build an image content part for multimodal messages.

    Reads the image file, encodes it as base64, and returns a
    langchain-compatible image_url content dict.

    Returns None if the image cannot be loaded.
    """
    path = Path(image_path)
    if not path.exists():
        logger.warning("Image file not found: %s", image_path)
        return None

    mime_type = mimetypes.guess_type(str(path))[0] or "image/jpeg"

    try:
        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{image_data}",
            },
        }
    except Exception as e:
        logger.warning("Failed to load image %s: %s", image_path, e)
        return None


def _call_llm_text(
    model_name: str,
    temperature: float,
    prompt: str,
) -> str:
    """Invoke the LLM with a system prompt and a text-only user prompt."""
    llm = _create_llm(model_name, temperature)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    return response.content.strip()


def _call_llm_multimodal(
    model_name: str,
    temperature: float,
    prompt: str,
    image_path: str | None = None,
) -> str:
    """Invoke the LLM with an optional image alongside text.

    If image_path is provided and valid, sends a multimodal message.
    Otherwise falls back to text-only.
    """
    llm = _create_llm(model_name, temperature)

    content_parts: list[dict | str] = []

    # Add image if available
    if image_path:
        img_content = _build_image_content(image_path)
        if img_content:
            content_parts.append(img_content)
            logger.info("Including image in multimodal request: %s", image_path)

    # Add text prompt
    content_parts.append({"type": "text", "text": prompt})

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=content_parts),
    ]
    response = llm.invoke(messages)
    return response.content.strip()


# ---------------------------------------------------------------------------
# Node factory functions
# ---------------------------------------------------------------------------


def make_parse_imaging(model_name: str, temperature: float):
    """Factory for the parse_imaging node function."""

    def parse_imaging(state: SecondaryOversightState) -> dict:
        """Extract ALL visible findings from report text (and image if available).

        This is the multimodal node — it sends both the image and report
        text to the model for comprehensive finding extraction.
        """
        logger.info("Node [parse_imaging] processing input")
        image_path = state.get("image_path", "") or ""

        prompt = PARSE_IMAGING_PROMPT.format(report_text=state["report_text"])

        if image_path:
            result = _call_llm_multimodal(model_name, temperature, prompt, image_path)
        else:
            result = _call_llm_text(model_name, temperature, prompt)

        logger.info("Node [parse_imaging] completed (len=%d)", len(result))
        return {"parsed_findings": result}

    return parse_imaging


def make_identify_findings(model_name: str, temperature: float):
    """Factory for the identify_findings node function."""

    def identify_findings(state: SecondaryOversightState) -> dict:
        """Compare extracted findings against the report to identify gaps."""
        logger.info("Node [identify_findings] processing input")

        prompt = IDENTIFY_FINDINGS_PROMPT.format(
            parsed_findings=state["parsed_findings"],
            report_text=state["report_text"],
        )

        result = _call_llm_text(model_name, temperature, prompt)
        logger.info("Node [identify_findings] completed (len=%d)", len(result))
        return {"missed_findings": result}

    return identify_findings


def make_generate_questions(model_name: str, temperature: float):
    """Factory for the generate_questions node function."""

    def generate_questions(state: SecondaryOversightState) -> dict:
        """Transform missed findings into gentle, non-alarming patient questions."""
        logger.info("Node [generate_questions] processing input")

        # If no missed findings, return a reassuring message
        missed = state.get("missed_findings", "")
        if (
            not missed
            or "no unaddressed findings" in missed.lower()
            or missed.strip() == ""
        ):
            logger.info("No missed findings to generate questions for")
            return {
                "patient_questions": (
                    "Great news — the review did not identify any additional "
                    "findings beyond what your doctor has already addressed. "
                    "No extra questions needed for your next visit!"
                )
            }

        prompt = GENERATE_QUESTIONS_PROMPT.format(missed_findings=missed)
        result = _call_llm_text(model_name, temperature, prompt)
        logger.info("Node [generate_questions] completed (len=%d)", len(result))
        return {"patient_questions": result}

    return generate_questions
