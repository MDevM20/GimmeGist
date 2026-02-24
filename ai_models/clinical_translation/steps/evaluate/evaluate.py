"""Evaluate step: computes groundedness (faithfulness) and readability metrics.

Metrics:
1. Faithfulness (DeepEval) — measures if the output stays grounded to the input
2. Readability (textstat) — Flesch Reading Ease, Flesch-Kincaid Grade Level
3. Simplification Score — composite 0-1 score combining readability signals

This step produces metrics and chart artifacts. The orchestrator handles
logging them to MLflow.
"""

import json
import logging
import os
from pathlib import Path

import textstat
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

from constants import (
    DEFAULT_FAITHFULNESS_THRESHOLD,
    LABEL_CAUSE,
    LABEL_LOCATION,
    LABEL_TREATMENT,
    TARGET_FLESCH_READING_EASE_MIN,
    TARGET_GRADE_LEVEL_MAX,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Readability metrics
# ---------------------------------------------------------------------------


def compute_readability(text: str) -> dict:
    """Compute readability metrics for a piece of text.

    Returns:
        Dict with flesch_reading_ease, flesch_kincaid_grade, gunning_fog,
        avg_sentence_length, avg_word_length, and simplification_score.
    """
    fre = textstat.flesch_reading_ease(text)
    fkg = textstat.flesch_kincaid_grade(text)
    gf = textstat.gunning_fog(text)
    avg_sentence_len = textstat.avg_sentence_length(text)

    # Compute average word length manually
    words = text.split()
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)

    # Simplification score: 0-1 composite
    # Higher is simpler/more readable
    fre_score = min(max(fre / 100.0, 0.0), 1.0)  # Normalize FRE to 0-1
    grade_score = min(max(1.0 - (fkg / 16.0), 0.0), 1.0)  # Lower grade = better
    word_len_score = min(max(1.0 - ((avg_word_len - 3.0) / 7.0), 0.0), 1.0)

    simplification_score = fre_score * 0.4 + grade_score * 0.4 + word_len_score * 0.2

    return {
        "flesch_reading_ease": round(fre, 2),
        "flesch_kincaid_grade": round(fkg, 2),
        "gunning_fog": round(gf, 2),
        "avg_sentence_length": round(avg_sentence_len, 2),
        "avg_word_length": round(avg_word_len, 2),
        "simplification_score": round(simplification_score, 4),
    }


# ---------------------------------------------------------------------------
# Faithfulness / groundedness metrics
# ---------------------------------------------------------------------------


def compute_faithfulness(
    clinical_input: str,
    model_output: str,
    judge_model: str = "gemini/gemini-2.0-flash",
    threshold: float = DEFAULT_FAITHFULNESS_THRESHOLD,
) -> dict:
    """Compute faithfulness (groundedness) of model output against clinical input.

    Uses DeepEval's FaithfulnessMetric with the original clinical text as
    retrieval_context — the generated output must be factually grounded
    in the source material.

    Args:
        clinical_input: The original clinical text (source of truth).
        model_output: The model's simplified output.
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
        input=clinical_input,
        actual_output=model_output,
        retrieval_context=[clinical_input],
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


def format_model_output(cause: str, location: str, treatment: str) -> str:
    """Format the three model outputs into a single combined string."""
    return (
        f"{LABEL_CAUSE}: {cause}\n"
        f"{LABEL_LOCATION}: {location}\n"
        f"{LABEL_TREATMENT}: {treatment}"
    )


def evaluate_single(
    clinical_input: str,
    cause: str,
    location: str,
    treatment: str,
    judge_model: str = "gemini/gemini-2.0-flash",
    faithfulness_threshold: float = DEFAULT_FAITHFULNESS_THRESHOLD,
) -> dict:
    """Run full evaluation on a single sample.

    Returns combined metrics dict with both readability and faithfulness.
    """
    combined_output = format_model_output(cause, location, treatment)

    # Readability on combined output
    readability = compute_readability(combined_output)

    # Per-section readability
    cause_readability = compute_readability(cause)
    location_readability = compute_readability(location)
    treatment_readability = compute_readability(treatment)

    # Faithfulness on combined output
    faithfulness = compute_faithfulness(
        clinical_input=clinical_input,
        model_output=combined_output,
        judge_model=judge_model,
        threshold=faithfulness_threshold,
    )

    return {
        # Combined metrics
        **{f"combined_{k}": v for k, v in readability.items()},
        **faithfulness,
        # Per-section readability
        "cause_simplification_score": cause_readability["simplification_score"],
        "location_simplification_score": location_readability["simplification_score"],
        "treatment_simplification_score": treatment_readability["simplification_score"],
        "cause_flesch_reading_ease": cause_readability["flesch_reading_ease"],
        "location_flesch_reading_ease": location_readability["flesch_reading_ease"],
        "treatment_flesch_reading_ease": treatment_readability["flesch_reading_ease"],
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
            clinical_input, cause, location, treatment
        judge_model: LLM model for the faithfulness judge.
        faithfulness_threshold: Minimum passing threshold.
        report_dir: Directory to save the evaluation report. If None, uses 'reports/'.

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
                clinical_input=r["clinical_input"],
                cause=r["cause"],
                location=r["location"],
                treatment=r["treatment"],
                judge_model=judge_model,
                faithfulness_threshold=faithfulness_threshold,
            )
            ev["sample_index"] = i
            ev["clinical_input"] = r["clinical_input"]
            ev["cause"] = r["cause"]
            ev["location"] = r["location"]
            ev["treatment"] = r["treatment"]
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
        # Faithfulness
        "avg_faithfulness_score": _avg("faithfulness_score"),
        "faithfulness_pass_rate": round(
            sum(1 for e in valid_evals if e.get("faithfulness_passed")) / n_valid, 4
        ),
        # Overall readability
        "avg_flesch_reading_ease": _avg("combined_flesch_reading_ease"),
        "avg_flesch_kincaid_grade": _avg("combined_flesch_kincaid_grade"),
        "avg_gunning_fog": _avg("combined_gunning_fog"),
        "avg_simplification_score": _avg("combined_simplification_score"),
        # Per-section simplification
        "avg_cause_simplification": _avg("cause_simplification_score"),
        "avg_location_simplification": _avg("location_simplification_score"),
        "avg_treatment_simplification": _avg("treatment_simplification_score"),
        # Readability targets
        "meets_reading_ease_target": _avg("combined_flesch_reading_ease")
        >= TARGET_FLESCH_READING_EASE_MIN,
        "meets_grade_level_target": _avg("combined_flesch_kincaid_grade")
        <= TARGET_GRADE_LEVEL_MAX,
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
        "# Clinical Translation — Evaluation Report",
        "",
        "## Summary Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Samples Evaluated | {aggregate['n_evaluated']} / {aggregate['n_samples']} |",
        f"| Errors | {aggregate['n_errors']} |",
        "",
        "### Faithfulness (Groundedness)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Avg Faithfulness Score | {aggregate['avg_faithfulness_score']} |",
        f"| Pass Rate (≥ threshold) | {aggregate['faithfulness_pass_rate']:.1%} |",
        "",
        "### Readability",
        "",
        "| Metric | Value | Target |",
        "|--------|-------|--------|",
        f"| Avg Flesch Reading Ease | {aggregate['avg_flesch_reading_ease']} | ≥ {TARGET_FLESCH_READING_EASE_MIN} |",
        f"| Avg Flesch-Kincaid Grade | {aggregate['avg_flesch_kincaid_grade']} | ≤ {TARGET_GRADE_LEVEL_MAX} |",
        f"| Avg Gunning Fog Index | {aggregate['avg_gunning_fog']} | — |",
        f"| Avg Simplification Score | {aggregate['avg_simplification_score']} | — |",
        f"| Meets Reading Ease Target | {'✅' if aggregate['meets_reading_ease_target'] else '❌'} | |",
        f"| Meets Grade Level Target | {'✅' if aggregate['meets_grade_level_target'] else '❌'} | |",
        "",
        "### Per-Section Simplification",
        "",
        "| Section | Avg Simplification Score |",
        "|---------|------------------------|",
        f"| Cause | {aggregate['avg_cause_simplification']} |",
        f"| Location | {aggregate['avg_location_simplification']} |",
        f"| Treatment | {aggregate['avg_treatment_simplification']} |",
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
                f"**Clinical Input:** {sample.get('clinical_input', 'N/A')}",
                "",
                f"**The Cause:** {sample.get('cause', 'N/A')}",
                "",
                f"**The Location:** {sample.get('location', 'N/A')}",
                "",
                f"**The Goal/Potential Treatment:** {sample.get('treatment', 'N/A')}",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Faithfulness | {sample.get('faithfulness_score', 'N/A')} |",
                f"| Simplification Score | {sample.get('combined_simplification_score', 'N/A')} |",
                f"| Flesch Reading Ease | {sample.get('combined_flesch_reading_ease', 'N/A')} |",
                f"| Grade Level | {sample.get('combined_flesch_kincaid_grade', 'N/A')} |",
                "",
            ]
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
