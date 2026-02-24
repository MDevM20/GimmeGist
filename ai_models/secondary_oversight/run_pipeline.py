"""Secondary Oversight Pipeline — Main Orchestrator.

Orchestrates the full pipeline:
    1. Load environment (.secrets.env → .settings.env)
    2. Ingest evaluation data (ReXErr-v1 or synthetic demo)
    3. Split into indexes
    4. Skip feature transform (LLM model)
    5. Build LangGraph model
    6. Invoke graph on test samples
    7. Evaluate (finding capture + tone + readability)
    8. Log everything to MLflow
    9. Export report
"""

import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 1. Load environment — secrets first, then settings
# ---------------------------------------------------------------------------
_project_root = Path(__file__).parent
load_dotenv(_project_root / ".secrets.env", override=True)
load_dotenv(_project_root / ".settings.env", override=True)

# Ensure project root is on sys.path for step imports
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import mlflow

from constants import (
    MLFLOW_ARTIFACT_PATH,
    MLFLOW_MODEL_NAME,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_pipeline")

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
MODEL_NAME = os.getenv("MODEL_NAME", "medgemma-27b-img-latest")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))
MLFLOW_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT_NAME", "secondary_oversight")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "mlruns")
EVAL_DATASET = os.getenv("EVAL_DATASET", "synthetic_demo")
EVAL_N_SAMPLES = int(os.getenv("EVAL_N_SAMPLES", "10"))
EVAL_JUDGE_MODEL = os.getenv("EVAL_JUDGE_MODEL", "gemini/gemini-2.0-flash")
IMAGE_DIR = os.getenv("IMAGE_DIR", ".cache/images")
REXERR_DATA_DIR = os.getenv("REXERR_DATA_DIR", ".cache/datasets/rexerr")
REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "reports")


def run_pipeline():
    """Execute the full secondary oversight pipeline."""
    logger.info("=" * 60)
    logger.info("Secondary Oversight Pipeline — Starting")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 2. Ingest
    # ------------------------------------------------------------------
    logger.info("Step 1/6: Ingest")
    from steps.ingest.ingest import ingest

    data = ingest(
        source=EVAL_DATASET,
        n_samples=EVAL_N_SAMPLES,
        rexerr_data_dir=REXERR_DATA_DIR,
        image_dir=IMAGE_DIR,
    )

    # ------------------------------------------------------------------
    # 3. Split
    # ------------------------------------------------------------------
    logger.info("Step 2/6: Split")
    from steps.split.split import split

    indexes = split(data)
    test_data = [data[i] for i in indexes["test"]]
    logger.info("Test set: %d samples", len(test_data))

    # ------------------------------------------------------------------
    # 4. Transform (pass-through)
    # ------------------------------------------------------------------
    logger.info("Step 3/6: Transform (pass-through)")
    from steps.features.transform import transform

    transform()

    # ------------------------------------------------------------------
    # 5. Build Model (LangGraph)
    # ------------------------------------------------------------------
    logger.info("Step 4/6: Build LangGraph model")
    from steps.model.model import build_graph

    graph = build_graph(model_name=MODEL_NAME, temperature=TEMPERATURE)

    # ------------------------------------------------------------------
    # Set up MLflow
    # ------------------------------------------------------------------
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    with mlflow.start_run(run_name="secondary_oversight_run") as run:
        run_id = run.info.run_id
        logger.info("MLflow run started: %s", run_id)

        # Log parameters
        mlflow.log_params(
            {
                "model_name": MODEL_NAME,
                "temperature": TEMPERATURE,
                "max_output_tokens": MAX_OUTPUT_TOKENS,
                "eval_dataset": EVAL_DATASET,
                "eval_n_samples": EVAL_N_SAMPLES,
                "eval_judge_model": EVAL_JUDGE_MODEL,
                "graph_nodes": "parse_imaging → identify_findings → generate_questions",
            }
        )

        # Log split indexes
        split_path = Path(REPORT_OUTPUT_DIR) / "split_indexes.json"
        split_path.parent.mkdir(parents=True, exist_ok=True)
        with open(split_path, "w") as f:
            json.dump(indexes, f)
        mlflow.log_artifact(str(split_path))

        # ------------------------------------------------------------------
        # 6. Invoke graph on test samples
        # ------------------------------------------------------------------
        logger.info("Step 5/6: Running graph on %d test samples", len(test_data))
        results = []
        for i, sample in enumerate(test_data):
            logger.info("Processing sample %d/%d", i + 1, len(test_data))
            try:
                output = graph.invoke(
                    {
                        "report_text": sample["report_text"],
                        "image_path": sample.get("image_path", "") or "",
                        "parsed_findings": "",
                        "missed_findings": "",
                        "patient_questions": "",
                    }
                )
                results.append(
                    {
                        "report_text": sample["report_text"],
                        "original_report": sample.get("original_report", ""),
                        "missed_findings_gt": sample.get("missed_findings", []),
                        "image_path": sample.get("image_path", ""),
                        "parsed_findings": output.get("parsed_findings", ""),
                        "model_missed_findings": output.get("missed_findings", ""),
                        "patient_questions": output.get("patient_questions", ""),
                    }
                )
            except Exception as e:
                logger.error("Failed to process sample %d: %s", i, e)
                results.append(
                    {
                        "report_text": sample["report_text"],
                        "original_report": sample.get("original_report", ""),
                        "missed_findings_gt": sample.get("missed_findings", []),
                        "image_path": sample.get("image_path", ""),
                        "parsed_findings": f"[ERROR: {e}]",
                        "model_missed_findings": f"[ERROR: {e}]",
                        "patient_questions": f"[ERROR: {e}]",
                    }
                )

        # Save raw results
        results_path = Path(REPORT_OUTPUT_DIR) / "raw_results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        mlflow.log_artifact(str(results_path))

        # ------------------------------------------------------------------
        # 7. Evaluate
        # ------------------------------------------------------------------
        logger.info("Step 6/6: Evaluate")
        from steps.evaluate.evaluate import evaluate_batch

        # Filter out error results for evaluation
        valid_results = [
            r
            for r in results
            if not str(r.get("parsed_findings", "")).startswith("[ERROR")
        ]
        logger.info("Evaluating %d valid results", len(valid_results))

        metrics = evaluate_batch(
            results=valid_results,
            judge_model=EVAL_JUDGE_MODEL,
            report_dir=REPORT_OUTPUT_DIR,
        )

        # ------------------------------------------------------------------
        # Log metrics to MLflow
        # ------------------------------------------------------------------
        mlflow_metrics = {
            k: v
            for k, v in metrics.items()
            if isinstance(v, (int, float)) and k != "n_samples"
        }
        # Convert bools to int for MLflow
        for k, v in list(mlflow_metrics.items()):
            if isinstance(v, bool):
                mlflow_metrics[k] = int(v)
        mlflow.log_metrics(mlflow_metrics)

        # Log report artifacts
        for rpath in metrics.get("report_paths", []):
            mlflow.log_artifact(rpath)

        # ------------------------------------------------------------------
        # Log the LangGraph model to MLflow
        # ------------------------------------------------------------------
        logger.info("Logging LangGraph model to MLflow")
        try:
            mlflow.langgraph.log_model(
                lc_model=graph,
                artifact_path=MLFLOW_ARTIFACT_PATH,
            )
            logger.info("LangGraph model logged to MLflow")
        except Exception as e:
            logger.warning(
                "Failed to log LangGraph model via mlflow.langgraph: %s. "
                "Falling back to pyfunc.",
                e,
            )
            try:
                mlflow.pyfunc.log_model(
                    artifact_path=MLFLOW_ARTIFACT_PATH,
                    python_model=graph,
                )
                logger.info("Model logged via mlflow.pyfunc fallback")
            except Exception as e2:
                logger.error("Failed to log model: %s", e2)

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        logger.info("=" * 60)
        logger.info("Pipeline Complete!")
        logger.info("MLflow Run ID: %s", run_id)
        logger.info("Experiment: %s", MLFLOW_EXPERIMENT)
        logger.info("-" * 60)
        logger.info("Key Metrics:")
        logger.info(
            "  Avg Finding Capture Score: %s",
            metrics.get("avg_finding_capture_score", "N/A"),
        )
        logger.info(
            "  Finding Capture Pass Rate: %s",
            metrics.get("finding_capture_pass_rate", "N/A"),
        )
        logger.info(
            "  Avg Tone Score: %s",
            metrics.get("avg_tone_score", "N/A"),
        )
        logger.info(
            "  Avg Flesch Reading Ease: %s",
            metrics.get("avg_flesch_reading_ease", "N/A"),
        )
        logger.info(
            "  Avg Simplification Score: %s",
            metrics.get("avg_simplification_score", "N/A"),
        )
        logger.info("-" * 60)
        logger.info("Reports saved to: %s", REPORT_OUTPUT_DIR)
        for rpath in metrics.get("report_paths", []):
            logger.info("  → %s", rpath)
        logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
