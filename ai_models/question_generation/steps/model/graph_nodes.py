"""LangGraph node implementations for question generation.

Each node calls MedGemma via ChatGoogleGenerativeAI to generate one
category of patient questions (understanding, treatment, lifestyle).

LLM instances are lazily created at invocation time so the graph can
be compiled without an API key (required for MLflow logging).
"""

import logging
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage

from steps.model.prompts import (
    LIFESTYLE_PROMPT,
    SYSTEM_PROMPT,
    TREATMENT_PROMPT,
    UNDERSTANDING_PROMPT,
)

logger = logging.getLogger(__name__)


class QuestionGenerationState(TypedDict):
    """State schema for the question generation graph."""

    medical_input: str
    health_data: str
    symptoms: str
    understanding_questions: str
    treatment_questions: str
    lifestyle_questions: str


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
    medical_input: str,
    health_data: str,
    symptoms: str,
) -> str:
    """Invoke the LLM with a system prompt and a formatted user prompt."""
    llm = _create_llm(model_name, temperature)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=prompt_template.format(
                medical_input=medical_input,
                health_data=health_data,
                symptoms=symptoms,
            )
        ),
    ]
    response = llm.invoke(messages)
    return response.content.strip()


def make_generate_understanding(model_name: str, temperature: float):
    """Factory for the generate_understanding node function."""

    def generate_understanding(state: QuestionGenerationState) -> dict:
        """Generate questions to help the patient understand their condition."""
        logger.info("Node [generate_understanding] processing input")
        result = _call_llm(
            model_name,
            temperature,
            UNDERSTANDING_PROMPT,
            state["medical_input"],
            state["health_data"],
            state["symptoms"],
        )
        logger.info("Node [generate_understanding] completed (len=%d)", len(result))
        return {"understanding_questions": result}

    return generate_understanding


def make_generate_treatment(model_name: str, temperature: float):
    """Factory for the generate_treatment node function."""

    def generate_treatment(state: QuestionGenerationState) -> dict:
        """Generate questions about treatment options and alternatives."""
        logger.info("Node [generate_treatment] processing input")
        result = _call_llm(
            model_name,
            temperature,
            TREATMENT_PROMPT,
            state["medical_input"],
            state["health_data"],
            state["symptoms"],
        )
        logger.info("Node [generate_treatment] completed (len=%d)", len(result))
        return {"treatment_questions": result}

    return generate_treatment


def make_generate_lifestyle(model_name: str, temperature: float):
    """Factory for the generate_lifestyle node function."""

    def generate_lifestyle(state: QuestionGenerationState) -> dict:
        """Generate questions about lifestyle modifications."""
        logger.info("Node [generate_lifestyle] processing input")
        result = _call_llm(
            model_name,
            temperature,
            LIFESTYLE_PROMPT,
            state["medical_input"],
            state["health_data"],
            state["symptoms"],
        )
        logger.info("Node [generate_lifestyle] completed (len=%d)", len(result))
        return {"lifestyle_questions": result}

    return generate_lifestyle
