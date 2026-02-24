"""Global constants for the clinical translation model."""

# State keys
KEY_CLINICAL_INPUT = "clinical_input"
KEY_CAUSE = "cause"
KEY_LOCATION = "location"
KEY_TREATMENT = "treatment"

# Output section labels
LABEL_CAUSE = "The Cause"
LABEL_LOCATION = "The Location"
LABEL_TREATMENT = "The Goal/Potential Treatment"

# Readability targets
TARGET_FLESCH_READING_EASE_MIN = 60.0  # "Plain English" threshold
TARGET_GRADE_LEVEL_MAX = 8.0  # Max grade level for general public

# MLflow
MLFLOW_MODEL_NAME = "clinical_translation_langgraph"
MLFLOW_ARTIFACT_PATH = "clinical_translation_model"

# Evaluation
DEFAULT_FAITHFULNESS_THRESHOLD = 0.7
