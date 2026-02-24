"""Global constants for the question generation model."""

# State keys — inputs
KEY_MEDICAL_INPUT = "medical_input"
KEY_HEALTH_DATA = "health_data"
KEY_SYMPTOMS = "symptoms"

# State keys — outputs (one per LangGraph node)
KEY_UNDERSTANDING_QUESTIONS = "understanding_questions"
KEY_TREATMENT_QUESTIONS = "treatment_questions"
KEY_LIFESTYLE_QUESTIONS = "lifestyle_questions"

# Output section labels
LABEL_UNDERSTANDING = "Understanding"
LABEL_TREATMENT = "Treatment"
LABEL_LIFESTYLE = "Lifestyle"

# MLflow
MLFLOW_MODEL_NAME = "question_generation_langgraph"
MLFLOW_ARTIFACT_PATH = "question_generation_model"

# Evaluation
DEFAULT_FAITHFULNESS_THRESHOLD = 0.7
