"""LangGraph node implementations for clinical translation.

Each node calls MedGemma via ChatGoogleGenerativeAI to process one
dimension of the clinical translation (cause, location, treatment).

LLM instances are lazily created at invocation time so the graph can
be compiled without an API key (required for MLflow logging).
"""

import logging
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage

from steps.model.prompts import (
    CAUSE_PROMPT,
    LOCATION_PROMPT,
    SYSTEM_PROMPT,
    TREATMENT_PROMPT,
)

logger = logging.getLogger(__name__)


class ClinicalTranslationState(TypedDict):
    """State schema for the clinical translation graph."""

    clinical_input: str
    cause: str
    location: str
    treatment: str


def _create_llm(model_name: str, temperature: float):
    """Create a ChatGoogleGenerativeAI instance (lazy, at call time)."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
    )


def _call_llm(
    model_name: str,
    temperature: float,
    prompt_template: str,
    clinical_input: str,
) -> str:
    """Invoke the LLM with a system prompt and a formatted user prompt."""
    llm = _create_llm(model_name, temperature)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt_template.format(clinical_input=clinical_input)),
    ]
    response = llm.invoke(messages)
    return response.content.strip()


def make_extract_cause(model_name: str, temperature: float):
    """Factory for the extract_cause node function."""

    def extract_cause(state: ClinicalTranslationState) -> dict:
        """Extract and simplify the cause from clinical text."""
        logger.info("Node [extract_cause] processing input")
        result = _call_llm(
            model_name, temperature, CAUSE_PROMPT, state["clinical_input"]
        )
        logger.info("Node [extract_cause] completed (len=%d)", len(result))
        return {"cause": result}

    return extract_cause


def make_extract_location(model_name: str, temperature: float):
    """Factory for the extract_location node function."""

    def extract_location(state: ClinicalTranslationState) -> dict:
        """Extract and simplify the location from clinical text."""
        logger.info("Node [extract_location] processing input")
        result = _call_llm(
            model_name, temperature, LOCATION_PROMPT, state["clinical_input"]
        )
        logger.info("Node [extract_location] completed (len=%d)", len(result))
        return {"location": result}

    return extract_location


def make_extract_treatment(model_name: str, temperature: float):
    """Factory for the extract_treatment node function."""

    def extract_treatment(state: ClinicalTranslationState) -> dict:
        """Extract and simplify the treatment from clinical text."""
        logger.info("Node [extract_treatment] processing input")
        result = _call_llm(
            model_name, temperature, TREATMENT_PROMPT, state["clinical_input"]
        )
        logger.info("Node [extract_treatment] completed (len=%d)", len(result))
        return {"treatment": result}

    return extract_treatment
