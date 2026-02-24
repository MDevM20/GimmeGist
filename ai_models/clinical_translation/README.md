# Clinical Translation Model

LangGraph-based MLflow model that translates complex clinical and specialty medical reports into accessible, patient-friendly summaries using **MedGemma 27B** (text-only) via the Google Gemini API.

## Architecture

The model uses a 3-node sequential **LangGraph** to decompose clinical text into three patient-facing dimensions:

```
START → extract_cause → extract_location → extract_treatment → END
```

| Node | Purpose |
|------|---------|
| `extract_cause` | Explains *what* is happening in simple terms |
| `extract_location` | Explains *where* in the body this occurs |
| `extract_treatment` | Describes typical treatment goals and approaches |

### Example

**Input:** *"Medial meniscal degeneration with new horizontal tear."*

**Output:**
- **The Cause:** The cushion in your knee is showing age-related wear and has developed a small split.
- **The Location:** This is on the inner side of your knee, a common area for these issues.
- **The Goal/Potential Treatment:** Treatment usually focuses on reducing swelling and strengthening surrounding muscles rather than immediate surgery.

## Evaluation

Two metric categories are computed via **DeepEval** and **textstat**:

### Faithfulness (Groundedness)
- Uses `FaithfulnessMetric` with a **Gemini** judge model
- Ensures the simplified output stays factually grounded to the original clinical text

### Readability
- **Flesch Reading Ease** (target: ≥ 60)
- **Flesch-Kincaid Grade Level** (target: ≤ 8)
- **Gunning Fog Index**
- **Custom Simplification Score** (0-1 composite)

### Dataset
Evaluation uses the **MedLane** dataset — 12,801+ aligned clinical ↔ simplified sentence pairs from [github.com/machinelearning4health/MedLane](https://github.com/machinelearning4health/MedLane).

## Setup

### Prerequisites
- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) package manager
- Google API key with Gemini / MedGemma access

### Install
```bash
cd ai_models/clinical_translation
uv sync
```

### Configure
1. Edit `.secrets.env` with your API key:
   ```
   GOOGLE_API_KEY=your-key-here
   ```
2. Review `.settings.env` for model and evaluation parameters.

### Run
```bash
uv run python run_pipeline.py
```

### Output
- **MLflow UI:** `mlflow ui` (from the project directory) to view runs, metrics, and logged models
- **Reports directory:** `reports/` contains:
  - `evaluation_report.md` — Human-readable summary
  - `evaluation_summary.json` — Aggregate metrics
  - `evaluation_detail.json` — Per-sample results
  - `raw_results.json` — Raw model outputs

## Project Structure

```
clinical_translation/
├── pyproject.toml              # Dependencies (managed by uv)
├── constants.py                # Global constants
├── run_pipeline.py             # Main orchestrator
├── .settings.env               # Non-sensitive configuration
├── .secrets.env                # API keys (DO NOT COMMIT)
├── README.md
└── steps/
    ├── model/
    │   ├── model.py            # Builds LangGraph
    │   ├── graph_nodes.py      # Node implementations
    │   └── prompts.py          # Prompt templates
    ├── evaluate/
    │   ├── evaluate.py         # Metrics + report generation
    │   └── dataset.py          # MedLane dataset loader
    ├── ingest/
    │   └── ingest.py           # Data ingestion
    ├── split/
    │   └── split.py            # Train/test splitting
    └── features/
        └── transform.py        # Pass-through (no FE needed)
```
