"""Model step: builds the LangGraph compiled graph for clinical translation.

This step defines the graph architecture but does NOT execute it.
The orchestrator (run_pipeline.py) handles invocation and MLflow logging.
"""

import logging

from langgraph.graph import END, START, StateGraph

from steps.model.graph_nodes import (
    ClinicalTranslationState,
    make_extract_cause,
    make_extract_location,
    make_extract_treatment,
)

logger = logging.getLogger(__name__)


def build_graph(
    model_name: str = "gemini-2.0-flash",
    temperature: float = 0.3,
):
    """Build and compile the clinical translation LangGraph.

    The graph has three sequential nodes:
        START → extract_cause → extract_location → extract_treatment → END

    Each node calls MedGemma to process one dimension of the clinical report.

    Args:
        model_name: The Google Generative AI model identifier.
        temperature: Sampling temperature for the LLM.

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    logger.info(
        "Building clinical translation graph (model=%s, temp=%s)",
        model_name,
        temperature,
    )

    graph = StateGraph(ClinicalTranslationState)

    # Add nodes — each is a factory-built function with the LLM baked in
    graph.add_node("extract_cause", make_extract_cause(model_name, temperature))
    graph.add_node("extract_location", make_extract_location(model_name, temperature))
    graph.add_node("extract_treatment", make_extract_treatment(model_name, temperature))

    # Define the sequential flow
    graph.add_edge(START, "extract_cause")
    graph.add_edge("extract_cause", "extract_location")
    graph.add_edge("extract_location", "extract_treatment")
    graph.add_edge("extract_treatment", END)

    compiled = graph.compile()
    logger.info("Clinical translation graph compiled successfully")

    return compiled
