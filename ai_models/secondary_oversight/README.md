# Secondary Oversight Model

LangGraph-based MLflow model that acts as a **secondary diagnostic safety net** using **MedGemma 27B (multimodal)** via the Google Gemini API. The model parses radiology imaging alongside diagnostic text to identify potential unaddressed findings. Instead of raw clinical findings (which could cause patient panic), the model surfaces **gentle, exploratory questions** for the patient's consultation agenda.

## Architecture

The model uses a 3-node sequential **LangGraph** for the multimodal diagnostic oversight pipeline:

```
START → parse_imaging → identify_findings → generate_questions → END
```

| Node | Purpose |
|------|---------|
| `parse_imaging` | Sends radiology image + report text to MedGemma multimodal to extract ALL visible findings |
| `identify_findings` | Compares extracted findings against the report to identify unaddressed/missed findings |
| `generate_questions` | Transforms each missed finding into a gentle, non-alarming patient question |

### Example

**Input report:** *"PA chest radiograph. The lungs are clear bilaterally. No pleural effusion. Normal heart size."*

**Missed findings detected:** Mild osteopenia, tortuous aorta

**Patient questions generated:**
- *"Doctor, are there any signs that my bones are becoming weak, and is that something we should keep an eye on?"*
- *"I was curious — did you notice anything about my main blood vessel that we should watch over time?"*

## Evaluation Strategy

Two metric dimensions are evaluated:

### 1. Finding Capture Rate (Primary)
- Uses **DeepEval GEval** with a custom `finding_capture` criterion
- Measures recall: what fraction of known missed findings did the model identify?
- Threshold: ≥ 0.6 to pass

### 2. Tone / Layman Language Quality
- **Non-Alarmist Tone** — DeepEval GEval rates if questions are gentle, non-alarming, exploratory (0-1)
- **Flesch Reading Ease** (target: ≥ 60)
- **Flesch-Kincaid Grade Level** (target: ≤ 8)
- **Simplification Score** (0-1 composite)

### Datasets

| Source | Description | Access |
|--------|-------------|--------|
| `synthetic_demo` | 10 hardcoded chest X-ray report pairs with known missed findings | Built-in (default) |
| `rexerr` | [ReXErr-v1](https://physionet.org/content/rexerr-v1/) — 26K+ chest X-ray reports with synthetically injected errors from 12 clinical categories | PhysioNet (credentialed) |

ReXErr-v1 pairs original and error reports from MIMIC-CXR, with errors designed by radiologists. The "errors sampled" column effectively represents findings that were missed or modified. For images, the MIMIC-CXR DICOM images must also be downloaded from PhysioNet.

## Setup

### Prerequisites
- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) package manager
- Google API key with Gemini / MedGemma access

### Install
```bash
cd ai_models/secondary_oversight
uv sync
```

### Configure
1. Edit `.secrets.env` with your API key:
   ```
   GOOGLE_API_KEY=your-key-here
   ```
2. Review `.settings.env` for model and evaluation parameters.
3. To use ReXErr-v1: download CSVs from PhysioNet, place in `.cache/datasets/rexerr/`, and set `EVAL_DATASET=rexerr` in `.settings.env`.

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
secondary_oversight/
├── pyproject.toml              # Dependencies (managed by uv)
├── constants.py                # Global constants
├── run_pipeline.py             # Main orchestrator
├── .settings.env               # Non-sensitive configuration
├── .secrets.env                # API keys (DO NOT COMMIT)
├── README.md
└── steps/
    ├── model/
    │   ├── model.py            # Builds LangGraph
    │   ├── graph_nodes.py      # Multimodal node implementations
    │   └── prompts.py          # Prompt templates
    ├── evaluate/
    │   ├── evaluate.py         # Metrics + report generation
    │   └── dataset.py          # ReXErr-v1 + synthetic demo loader
    ├── ingest/
    │   └── ingest.py           # Data ingestion
    ├── split/
    │   └── split.py            # Train/test splitting
    └── features/
        └── transform.py        # Pass-through (no FE needed)
```
