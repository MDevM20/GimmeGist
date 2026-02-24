"""Model step: builds the LangGraph compiled graph for secondary oversight.

This step defines the graph architecture but does NOT execute it.
The orchestrator (run_pipeline.py) handles invocation and MLflow logging.
"""

import logging

from langgraph.graph import END, START, StateGraph

from steps.model.graph_nodes import (
    SecondaryOversightState,
    make_generate_questions,
    make_identify_findings,
    make_parse_imaging,
)

logger = logging.getLogger(__name__)


def build_graph(
    model_name: str = "medgemma-27b-img-latest",
    temperature: float = 0.3,
):
    """Build and compile the secondary oversight LangGraph.

    The graph has three sequential nodes:
        START → parse_imaging → identify_findings → generate_questions → END

    Each node calls MedGemma to process one stage of the diagnostic
    oversight pipeline.

    Args:
        model_name: The Google Generative AI model identifier.
        temperature: Sampling temperature for the LLM.

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    logger.info(
        "Building secondary oversight graph (model=%s, temp=%s)",
        model_name,
        temperature,
    )

    graph = StateGraph(SecondaryOversightState)

    # Add nodes — each is a factory-built function with the LLM baked in
    graph.add_node("parse_imaging", make_parse_imaging(model_name, temperature))
    graph.add_node("identify_findings", make_identify_findings(model_name, temperature))
    graph.add_node(
        "generate_questions", make_generate_questions(model_name, temperature)
    )

    # Define the sequential flow
    graph.add_edge(START, "parse_imaging")
    graph.add_edge("parse_imaging", "identify_findings")
    graph.add_edge("identify_findings", "generate_questions")
    graph.add_edge("generate_questions", END)

    compiled = graph.compile()
    logger.info("Secondary oversight graph compiled successfully")

    return compiled
