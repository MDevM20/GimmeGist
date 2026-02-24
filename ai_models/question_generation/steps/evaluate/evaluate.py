"""Evaluate step: computes groundedness (faithfulness) metrics for generated questions.

Metrics:
1. Faithfulness (DeepEval) — measures if generated questions stay grounded to the
   input medical data (reports, health data, symptoms). Each question should only
   reference facts present in or directly implied by the source material.

This step produces metrics and report artifacts. The orchestrator handles
logging them to MLflow.
"""

import json
import logging
from pathlib import Path

from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

from constants import (
    DEFAULT_FAITHFULNESS_THRESHOLD,
    LABEL_LIFESTYLE,
    LABEL_TREATMENT,
    LABEL_UNDERSTANDING,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Faithfulness / groundedness metrics
# ---------------------------------------------------------------------------


def compute_faithfulness(
    source_text: str,
    generated_output: str,
    judge_model: str = "gemini/gemini-2.0-flash",
    threshold: float = DEFAULT_FAITHFULNESS_THRESHOLD,
) -> dict:
    """Compute faithfulness (groundedness) of generated questions against source.

    Uses DeepEval's FaithfulnessMetric with the original medical data as
    retrieval_context — the generated questions must only reference facts
    present in the source material.

    Args:
        source_text: The combined medical input (report + health data + symptoms).
        generated_output: The model's generated questions.
        judge_model: LLM model to use as the evaluation judge.
        threshold: Minimum passing threshold for the metric.

    Returns:
        Dict with faithfulness_score, faithfulness_reason, and passed flag.
    """
    metric = FaithfulnessMetric(
        threshold=threshold,
        model=judge_model,
        include_reason=True,
    )

    test_case = LLMTestCase(
        input=source_text,
        actual_output=generated_output,
        retrieval_context=[source_text],
    )

    metric.measure(test_case)

    return {
        "faithfulness_score": round(metric.score, 4),
        "faithfulness_reason": metric.reason or "",
        "faithfulness_passed": metric.score >= threshold,
    }


# ---------------------------------------------------------------------------
# Combined evaluation
# ---------------------------------------------------------------------------


def format_model_output(
    understanding: str,
    treatment: str,
    lifestyle: str,
) -> str:
    """Format the three question categories into a single combined string."""
    return (
        f"{LABEL_UNDERSTANDING}:\n{understanding}\n\n"
        f"{LABEL_TREATMENT}:\n{treatment}\n\n"
        f"{LABEL_LIFESTYLE}:\n{lifestyle}"
    )


def evaluate_single(
    source_text: str,
    understanding_questions: str,
    treatment_questions: str,
    lifestyle_questions: str,
    judge_model: str = "gemini/gemini-2.0-flash",
    faithfulness_threshold: float = DEFAULT_FAITHFULNESS_THRESHOLD,
) -> dict:
    """Run full evaluation on a single sample.

    Evaluates faithfulness for the combined output and each individual category.

    Returns combined metrics dict.
    """
    combined_output = format_model_output(
        understanding_questions, treatment_questions, lifestyle_questions
    )

    # Combined faithfulness
    combined_faith = compute_faithfulness(
        source_text=source_text,
        generated_output=combined_output,
        judge_model=judge_model,
        threshold=faithfulness_threshold,
    )

    # Per-category faithfulness
    understanding_faith = compute_faithfulness(
        source_text=source_text,
        generated_output=understanding_questions,
        judge_model=judge_model,
        threshold=faithfulness_threshold,
    )
    treatment_faith = compute_faithfulness(
        source_text=source_text,
        generated_output=treatment_questions,
        judge_model=judge_model,
        threshold=faithfulness_threshold,
    )
    lifestyle_faith = compute_faithfulness(
        source_text=source_text,
        generated_output=lifestyle_questions,
        judge_model=judge_model,
        threshold=faithfulness_threshold,
    )

    return {
        # Combined
        **{f"combined_{k}": v for k, v in combined_faith.items()},
        # Per-category
        "understanding_faithfulness": understanding_faith["faithfulness_score"],
        "treatment_faithfulness": treatment_faith["faithfulness_score"],
        "lifestyle_faithfulness": lifestyle_faith["faithfulness_score"],
        "understanding_passed": understanding_faith["faithfulness_passed"],
        "treatment_passed": treatment_faith["faithfulness_passed"],
        "lifestyle_passed": lifestyle_faith["faithfulness_passed"],
    }


def evaluate_batch(
    results: list[dict],
    judge_model: str = "gemini/gemini-2.0-flash",
    faithfulness_threshold: float = DEFAULT_FAITHFULNESS_THRESHOLD,
    report_dir: str | None = None,
) -> dict:
    """Evaluate a batch of model results and produce aggregate metrics + report.

    Args:
        results: List of dicts, each with keys:
            source_text, understanding_questions, treatment_questions,
            lifestyle_questions
        judge_model: LLM model for the faithfulness judge.
        faithfulness_threshold: Minimum passing threshold.
        report_dir: Directory to save the evaluation report.

    Returns:
        Dict with aggregate metrics and report file paths.
    """
    report_dir = Path(report_dir or "reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    all_evals = []
    for i, r in enumerate(results):
        logger.info("Evaluating sample %d/%d", i + 1, len(results))
        try:
            ev = evaluate_single(
                source_text=r["source_text"],
                understanding_questions=r["understanding_questions"],
                treatment_questions=r["treatment_questions"],
                lifestyle_questions=r["lifestyle_questions"],
                judge_model=judge_model,
                faithfulness_threshold=faithfulness_threshold,
            )
            ev["sample_index"] = i
            ev["source_text"] = r["source_text"]
            ev["understanding_questions"] = r["understanding_questions"]
            ev["treatment_questions"] = r["treatment_questions"]
            ev["lifestyle_questions"] = r["lifestyle_questions"]
            all_evals.append(ev)
        except Exception as e:
            logger.error("Failed to evaluate sample %d: %s", i, e)
            all_evals.append({"sample_index": i, "error": str(e)})

    # Compute aggregate metrics
    valid_evals = [e for e in all_evals if "error" not in e]
    n_valid = len(valid_evals)

    if n_valid == 0:
        logger.warning("No valid evaluations to aggregate")
        return {"error": "No valid evaluations", "report_paths": []}

    def _avg(key):
        vals = [e[key] for e in valid_evals if isinstance(e.get(key), (int, float))]
        return round(sum(vals) / max(len(vals), 1), 4)

    aggregate = {
        "n_samples": len(results),
        "n_evaluated": n_valid,
        "n_errors": len(results) - n_valid,
        # Combined faithfulness
        "avg_faithfulness_score": _avg("combined_faithfulness_score"),
        "faithfulness_pass_rate": round(
            sum(1 for e in valid_evals if e.get("combined_faithfulness_passed"))
            / n_valid,
            4,
        ),
        # Per-category faithfulness
        "avg_understanding_faithfulness": _avg("understanding_faithfulness"),
        "avg_treatment_faithfulness": _avg("treatment_faithfulness"),
        "avg_lifestyle_faithfulness": _avg("lifestyle_faithfulness"),
        # Per-category pass rates
        "understanding_pass_rate": round(
            sum(1 for e in valid_evals if e.get("understanding_passed")) / n_valid,
            4,
        ),
        "treatment_pass_rate": round(
            sum(1 for e in valid_evals if e.get("treatment_passed")) / n_valid,
            4,
        ),
        "lifestyle_pass_rate": round(
            sum(1 for e in valid_evals if e.get("lifestyle_passed")) / n_valid,
            4,
        ),
    }

    # ---------------------------------------------------------------------------
    # Generate report files
    # ---------------------------------------------------------------------------
    report_paths = []

    # 1. Detailed JSON report
    detail_path = report_dir / "evaluation_detail.json"
    with open(detail_path, "w", encoding="utf-8") as f:
        json.dump(all_evals, f, indent=2, ensure_ascii=False)
    report_paths.append(str(detail_path))
    logger.info("Detailed report saved to %s", detail_path)

    # 2. Summary JSON report
    summary_path = report_dir / "evaluation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(aggregate, f, indent=2, ensure_ascii=False)
    report_paths.append(str(summary_path))
    logger.info("Summary report saved to %s", summary_path)

    # 3. Human-readable markdown report
    md_path = report_dir / "evaluation_report.md"
    _write_markdown_report(aggregate, valid_evals, md_path)
    report_paths.append(str(md_path))
    logger.info("Markdown report saved to %s", md_path)

    aggregate["report_paths"] = report_paths
    return aggregate


def _write_markdown_report(
    aggregate: dict,
    samples: list[dict],
    output_path: Path,
) -> None:
    """Write a human-readable markdown evaluation report."""
    lines = [
        "# Question Generation — Evaluation Report",
        "",
        "## Summary Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Samples Evaluated | {aggregate['n_evaluated']} / {aggregate['n_samples']} |",
        f"| Errors | {aggregate['n_errors']} |",
        "",
        "### Combined Faithfulness (Groundedness)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Avg Faithfulness Score | {aggregate['avg_faithfulness_score']} |",
        f"| Pass Rate (≥ threshold) | {aggregate['faithfulness_pass_rate']:.1%} |",
        "",
        "### Per-Category Faithfulness",
        "",
        "| Category | Avg Score | Pass Rate |",
        "|----------|-----------|-----------|",
        f"| Understanding | {aggregate['avg_understanding_faithfulness']} | {aggregate['understanding_pass_rate']:.1%} |",
        f"| Treatment | {aggregate['avg_treatment_faithfulness']} | {aggregate['treatment_pass_rate']:.1%} |",
        f"| Lifestyle | {aggregate['avg_lifestyle_faithfulness']} | {aggregate['lifestyle_pass_rate']:.1%} |",
        "",
        "---",
        "",
        "## Sample Results",
        "",
    ]

    # Show up to 10 sample results
    for sample in samples[:10]:
        idx = sample.get("sample_index", "?")
        lines.extend(
            [
                f"### Sample {idx}",
                "",
                f"**Source Text:** {sample.get('source_text', 'N/A')[:200]}...",
                "",
                f"**Understanding Questions:**",
                f"{sample.get('understanding_questions', 'N/A')}",
                "",
                f"**Treatment Questions:**",
                f"{sample.get('treatment_questions', 'N/A')}",
                "",
                f"**Lifestyle Questions:**",
                f"{sample.get('lifestyle_questions', 'N/A')}",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Combined Faithfulness | {sample.get('combined_faithfulness_score', 'N/A')} |",
                f"| Understanding Faithfulness | {sample.get('understanding_faithfulness', 'N/A')} |",
                f"| Treatment Faithfulness | {sample.get('treatment_faithfulness', 'N/A')} |",
                f"| Lifestyle Faithfulness | {sample.get('lifestyle_faithfulness', 'N/A')} |",
                "",
            ]
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
