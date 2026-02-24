"""Model step: builds the LangGraph compiled graph for question generation.

This step defines the graph architecture but does NOT execute it.
The orchestrator (run_pipeline.py) handles invocation and MLflow logging.
"""

import logging

from langgraph.graph import END, START, StateGraph

from steps.model.graph_nodes import (
    QuestionGenerationState,
    make_generate_lifestyle,
    make_generate_treatment,
    make_generate_understanding,
)

logger = logging.getLogger(__name__)


def build_graph(
    model_name: str = "medgemma-27b-text-latest",
    temperature: float = 0.4,
):
    """Build and compile the question generation LangGraph.

    The graph has three sequential nodes:
        START → generate_understanding → generate_treatment → generate_lifestyle → END

    Each node calls MedGemma to generate one category of patient questions.

    Args:
        model_name: The Google Generative AI model identifier.
        temperature: Sampling temperature for the LLM.

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    logger.info(
        "Building question generation graph (model=%s, temp=%s)",
        model_name,
        temperature,
    )

    graph = StateGraph(QuestionGenerationState)

    # Add nodes — each is a factory-built function with the LLM baked in
    graph.add_node(
        "generate_understanding",
        make_generate_understanding(model_name, temperature),
    )
    graph.add_node(
        "generate_treatment",
        make_generate_treatment(model_name, temperature),
    )
    graph.add_node(
        "generate_lifestyle",
        make_generate_lifestyle(model_name, temperature),
    )

    # Define the sequential flow
    graph.add_edge(START, "generate_understanding")
    graph.add_edge("generate_understanding", "generate_treatment")
    graph.add_edge("generate_treatment", "generate_lifestyle")
    graph.add_edge("generate_lifestyle", END)

    compiled = graph.compile()
    logger.info("Question generation graph compiled successfully")

    return compiled
