# Question Generation Model

LangGraph-based MLflow model that generates **strategic patient questions** from medical reports, health data, and symptoms using **MedGemma 27B** (text-only) via the Google Gemini API.

## Architecture

The model uses a 3-node sequential **LangGraph** to generate prioritized questions across three categories:

```
START → generate_understanding → generate_treatment → generate_lifestyle → END
```

| Node | Purpose |
|------|---------|
| `generate_understanding` | Questions about what the condition means, its severity, causes |
| `generate_treatment` | Questions about treatment options, alternatives, timelines |
| `generate_lifestyle` | Questions about lifestyle modifications, things to avoid |

### Input

The model accepts three types of input:
- **Medical Report** — Clinical text, diagnosis, imaging results
- **Health Data** — Vitals, lab results, wearable metrics
- **Symptoms** — Patient-reported or transcribed symptoms

### Example

**Input:** *"Medial meniscal degeneration with new horizontal tear. Mild osteoarthritis."*

**Output:**
- **Understanding:**
  1. Does the "wear and tear" mean my knee is aging faster than normal, and what can I do to protect it?
  2. How serious is this tear — could it get worse on its own?
- **Treatment:**
  1. Can we try physical therapy first, and which muscles should I focus on to support the joint?
  2. At what point would surgery become necessary?
- **Lifestyle:**
  1. Are there specific movements, like squatting, that I should avoid right now?
  2. Should I change my exercise routine, and what activities are safe?

## Evaluation

Uses **DeepEval** for groundedness evaluation:

### Faithfulness (Groundedness)
- Uses `FaithfulnessMetric` with a **Gemini** judge model
- Ensures generated questions stay factually grounded to the input medical data
- Evaluated both combined and per-category (understanding, treatment, lifestyle)

### Dataset
Evaluation uses the **MedQuAD** dataset — 47,000+ medical Q&A pairs from 12 NIH websites, available on [HuggingFace](https://huggingface.co/datasets/keivalya/MedQuad-MedicalQnADataset).

## Setup

### Prerequisites
- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) package manager
- Google API key with Gemini / MedGemma access

### Install
```bash
cd ai_models/question_generation
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
question_generation/
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
    │   └── dataset.py          # MedQuAD dataset loader
    ├── ingest/
    │   └── ingest.py           # Data ingestion
    ├── split/
    │   └── split.py            # Train/test splitting
    └── features/
        └── transform.py        # Pass-through (no FE needed)
```
