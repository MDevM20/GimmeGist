"""Evaluate step: measures finding capture rate and tone/readability quality.

Two evaluation dimensions:

1. Finding Capture — does the model identify the missed findings?
   - Uses DeepEval GEval with a custom "finding_overlap" criterion
   - Computes recall/precision-style metrics

2. Tone / Layman Language — are the patient questions non-alarming and readable?
   - Readability via textstat (Flesch Reading Ease, Flesch-Kincaid Grade)
   - Non-alarmist tone via DeepEval GEval with custom criteria
   - Simplification score (0-1 composite)

This step produces metrics and chart artifacts. The orchestrator handles
logging them to MLflow.
"""

import json
import logging
from pathlib import Path

import textstat
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from constants import (
    DEFAULT_FINDING_CAPTURE_THRESHOLD,
    DEFAULT_TONE_THRESHOLD,
    TARGET_FLESCH_READING_EASE_MIN,
    TARGET_GRADE_LEVEL_MAX,
    TARGET_TONE_SCORE_MIN,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Readability metrics
# ---------------------------------------------------------------------------


def compute_readability(text: str) -> dict:
    """Compute readability metrics for patient-facing text.

    Returns:
        Dict with flesch_reading_ease, flesch_kincaid_grade, gunning_fog,
        avg_sentence_length, avg_word_length, and simplification_score.
    """
    fre = textstat.flesch_reading_ease(text)
    fkg = textstat.flesch_kincaid_grade(text)
    gf = textstat.gunning_fog(text)
    avg_sentence_len = textstat.avg_sentence_length(text)

    # Compute average word length
    words = text.split()
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)

    # Simplification score: 0-1 composite (higher = simpler/more readable)
    fre_score = min(max(fre / 100.0, 0.0), 1.0)
    grade_score = min(max(1.0 - (fkg / 16.0), 0.0), 1.0)
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
# Finding capture metrics (via DeepEval GEval)
# ---------------------------------------------------------------------------


def compute_finding_capture(
    ground_truth_findings: list[str],
    model_missed_findings: str,
    judge_model: str = "gemini/gemini-2.0-flash",
    threshold: float = DEFAULT_FINDING_CAPTURE_THRESHOLD,
) -> dict:
    """Evaluate how well the model captured the ground-truth missed findings.

    Uses DeepEval's GEval with a custom criterion that measures overlap
    between the model's identified findings and the known ground-truth.

    Args:
        ground_truth_findings: List of known missed findings (ground truth).
        model_missed_findings: The model's output from the identify_findings node.
        judge_model: LLM model to use as the evaluation judge.
        threshold: Minimum passing threshold for the metric.

    Returns:
        Dict with finding_capture_score, finding_capture_reason, and passed flag.
    """
    ground_truth_str = "\n".join(f"- {f}" for f in ground_truth_findings)

    metric = GEval(
        name="finding_capture",
        criteria=(
            "Evaluate how well the 'actual output' captures the missed findings "
            "listed in the 'expected output'. Score based on: "
            "1) What fraction of the expected missed findings are identified "
            "(recall)? 2) Are the identified findings clinically equivalent to "
            "the expected ones, even if worded differently? "
            "A score of 1.0 means ALL expected missed findings were captured. "
            "A score of 0.0 means NONE were captured."
        ),
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        model=judge_model,
        threshold=threshold,
    )

    test_case = LLMTestCase(
        input="Identify missed findings in radiology report",
        actual_output=model_missed_findings,
        expected_output=ground_truth_str,
    )

    metric.measure(test_case)

    return {
        "finding_capture_score": round(metric.score, 4),
        "finding_capture_reason": metric.reason or "",
        "finding_capture_passed": metric.score >= threshold,
    }


# ---------------------------------------------------------------------------
# Tone / Non-alarmist metrics (via DeepEval GEval)
# ---------------------------------------------------------------------------


def compute_tone_quality(
    patient_questions: str,
    judge_model: str = "gemini/gemini-2.0-flash",
    threshold: float = DEFAULT_TONE_THRESHOLD,
) -> dict:
    """Evaluate if the patient questions are gentle and non-alarming.

    Uses DeepEval's GEval with a custom criterion measuring tone quality.

    Args:
        patient_questions: The model's generated patient questions.
        judge_model: LLM model for the evaluation judge.
        threshold: Minimum passing threshold.

    Returns:
        Dict with tone_score, tone_reason, and passed flag.
    """
    metric = GEval(
        name="non_alarmist_tone",
        criteria=(
            "Evaluate whether the patient questions in the 'actual output' are "
            "gentle, non-alarming, and exploratory. Score based on: "
            "1) Do the questions avoid medical jargon? "
            "2) Do they use softening language (e.g., 'I was wondering', "
            "'could we check')? "
            "3) Do they avoid implying urgency, danger, or specific diagnoses? "
            "4) Would a worried patient feel calmer, not more anxious, "
            "after reading these questions? "
            "5) Are they framed as curious exploration, not demanding answers? "
            "A score of 1.0 means perfectly gentle and reassuring. "
            "A score of 0.0 means alarming and panic-inducing."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        model=judge_model,
        threshold=threshold,
    )

    test_case = LLMTestCase(
        input="Generate gentle patient questions for missed radiology findings",
        actual_output=patient_questions,
    )

    metric.measure(test_case)

    return {
        "tone_score": round(metric.score, 4),
        "tone_reason": metric.reason or "",
        "tone_passed": metric.score >= threshold,
    }


# ---------------------------------------------------------------------------
# Combined single-sample evaluation
# ---------------------------------------------------------------------------


def evaluate_single(
    report_text: str,
    missed_findings_gt: list[str],
    model_missed_findings: str,
    patient_questions: str,
    judge_model: str = "gemini/gemini-2.0-flash",
    finding_threshold: float = DEFAULT_FINDING_CAPTURE_THRESHOLD,
    tone_threshold: float = DEFAULT_TONE_THRESHOLD,
) -> dict:
    """Run full evaluation on a single sample.

    Returns combined metrics dict with finding capture, tone, and readability.
    """
    # Finding capture
    capture = compute_finding_capture(
        ground_truth_findings=missed_findings_gt,
        model_missed_findings=model_missed_findings,
        judge_model=judge_model,
        threshold=finding_threshold,
    )

    # Tone quality
    tone = compute_tone_quality(
        patient_questions=patient_questions,
        judge_model=judge_model,
        threshold=tone_threshold,
    )

    # Readability of patient questions
    readability = compute_readability(patient_questions)

    return {
        **capture,
        **tone,
        **{f"questions_{k}": v for k, v in readability.items()},
    }


# ---------------------------------------------------------------------------
# Batch evaluation
# ---------------------------------------------------------------------------


def evaluate_batch(
    results: list[dict],
    judge_model: str = "gemini/gemini-2.0-flash",
    finding_threshold: float = DEFAULT_FINDING_CAPTURE_THRESHOLD,
    tone_threshold: float = DEFAULT_TONE_THRESHOLD,
    report_dir: str | None = None,
) -> dict:
    """Evaluate a batch of model results and produce aggregate metrics + report.

    Args:
        results: List of dicts, each with keys:
            report_text, missed_findings_gt, model_missed_findings,
            patient_questions
        judge_model: LLM model for the evaluation judge.
        finding_threshold: Minimum passing threshold for finding capture.
        tone_threshold: Minimum passing threshold for tone quality.
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
                report_text=r["report_text"],
                missed_findings_gt=r["missed_findings_gt"],
                model_missed_findings=r["model_missed_findings"],
                patient_questions=r["patient_questions"],
                judge_model=judge_model,
                finding_threshold=finding_threshold,
                tone_threshold=tone_threshold,
            )
            ev["sample_index"] = i
            ev["report_text"] = r["report_text"]
            ev["missed_findings_gt"] = r["missed_findings_gt"]
            ev["model_missed_findings"] = r["model_missed_findings"]
            ev["patient_questions"] = r["patient_questions"]
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
        # Finding capture
        "avg_finding_capture_score": _avg("finding_capture_score"),
        "finding_capture_pass_rate": round(
            sum(1 for e in valid_evals if e.get("finding_capture_passed")) / n_valid, 4
        ),
        # Tone quality
        "avg_tone_score": _avg("tone_score"),
        "tone_pass_rate": round(
            sum(1 for e in valid_evals if e.get("tone_passed")) / n_valid, 4
        ),
        # Readability of patient questions
        "avg_flesch_reading_ease": _avg("questions_flesch_reading_ease"),
        "avg_flesch_kincaid_grade": _avg("questions_flesch_kincaid_grade"),
        "avg_gunning_fog": _avg("questions_gunning_fog"),
        "avg_simplification_score": _avg("questions_simplification_score"),
        # Targets
        "meets_reading_ease_target": _avg("questions_flesch_reading_ease")
        >= TARGET_FLESCH_READING_EASE_MIN,
        "meets_grade_level_target": _avg("questions_flesch_kincaid_grade")
        <= TARGET_GRADE_LEVEL_MAX,
        "meets_tone_target": _avg("tone_score") >= (TARGET_TONE_SCORE_MIN / 5.0),
    }

    # ---------------------------------------------------------------------------
    # Generate report files
    # ---------------------------------------------------------------------------
    report_paths = []

    # 1. Detailed JSON report
    detail_path = report_dir / "evaluation_detail.json"
    with open(detail_path, "w", encoding="utf-8") as f:
        json.dump(all_evals, f, indent=2, ensure_ascii=False, default=str)
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
        "# Secondary Oversight — Evaluation Report",
        "",
        "## Summary Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Samples Evaluated | {aggregate['n_evaluated']} / {aggregate['n_samples']} |",
        f"| Errors | {aggregate['n_errors']} |",
        "",
        "### Finding Capture (Missed Finding Detection)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Avg Finding Capture Score | {aggregate['avg_finding_capture_score']} |",
        f"| Pass Rate (≥ threshold) | {aggregate['finding_capture_pass_rate']:.1%} |",
        "",
        "### Non-Alarmist Tone",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Avg Tone Score | {aggregate['avg_tone_score']} |",
        f"| Tone Pass Rate | {aggregate['tone_pass_rate']:.1%} |",
        f"| Meets Tone Target | {'✅' if aggregate['meets_tone_target'] else '❌'} |",
        "",
        "### Readability (Patient Questions)",
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
        "---",
        "",
        "## Sample Results",
        "",
    ]

    # Show up to 10 sample results
    for sample in samples[:10]:
        idx = sample.get("sample_index", "?")
        gt_findings = sample.get("missed_findings_gt", [])
        gt_str = ", ".join(gt_findings) if gt_findings else "N/A"
        lines.extend(
            [
                f"### Sample {idx}",
                "",
                f"**Report (excerpt):** {sample.get('report_text', 'N/A')[:200]}…",
                "",
                f"**Ground Truth Missed Findings:** {gt_str}",
                "",
                f"**Model Identified Findings:** {sample.get('model_missed_findings', 'N/A')[:300]}",
                "",
                f"**Patient Questions:** {sample.get('patient_questions', 'N/A')[:300]}",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Finding Capture | {sample.get('finding_capture_score', 'N/A')} |",
                f"| Tone Score | {sample.get('tone_score', 'N/A')} |",
                f"| Simplification | {sample.get('questions_simplification_score', 'N/A')} |",
                f"| Flesch Reading Ease | {sample.get('questions_flesch_reading_ease', 'N/A')} |",
                "",
            ]
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
