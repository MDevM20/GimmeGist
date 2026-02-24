"""Global constants for the secondary oversight model."""

# State keys
KEY_REPORT_TEXT = "report_text"
KEY_IMAGE_PATH = "image_path"
KEY_PARSED_FINDINGS = "parsed_findings"
KEY_MISSED_FINDINGS = "missed_findings"
KEY_PATIENT_QUESTIONS = "patient_questions"

# Output section labels
LABEL_PARSED_FINDINGS = "All Visible Findings"
LABEL_MISSED_FINDINGS = "Unaddressed Findings"
LABEL_PATIENT_QUESTIONS = "Suggested Questions for Your Doctor"

# Readability targets
TARGET_FLESCH_READING_EASE_MIN = 60.0  # "Plain English" threshold
TARGET_GRADE_LEVEL_MAX = 8.0  # Max grade level for general public

# Tone evaluation
TARGET_TONE_SCORE_MIN = 3.5  # Min acceptable non-alarmist tone (1-5 scale)

# MLflow
MLFLOW_MODEL_NAME = "secondary_oversight_langgraph"
MLFLOW_ARTIFACT_PATH = "secondary_oversight_model"

# Evaluation
DEFAULT_FINDING_CAPTURE_THRESHOLD = 0.6  # Min recall of missed findings
DEFAULT_TONE_THRESHOLD = 0.7
