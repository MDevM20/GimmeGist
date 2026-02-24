"""Prompt templates for the clinical translation LangGraph nodes."""

SYSTEM_PROMPT = """You are a medical communication specialist powered by MedGemma.
Your role is to translate complex clinical and medical terminology into clear,
empathetic, patient-friendly language.

Rules:
- Stay STRICTLY grounded to the provided clinical text. Never invent conditions,
  symptoms, or treatments not mentioned or directly implied by the input.
- Use everyday analogies and simple words (target: 6th-8th grade reading level).
- Be warm and reassuring without minimizing the condition.
- Use second person ("your") to address the patient directly.
- Keep each response to 1-3 sentences maximum.
"""

CAUSE_PROMPT = """Based on the following clinical text, explain THE CAUSE — what is
happening in the patient's body in simple, everyday language. Use analogies where
helpful (e.g., "cushion" for meniscus, "wear and tear" for degeneration).

Do NOT mention location or treatment — only explain what the condition IS and
what is causing it.

Clinical text: {clinical_input}

Respond with only the plain-language explanation of the cause, nothing else."""

LOCATION_PROMPT = """Based on the following clinical text, explain THE LOCATION —
where in the body this issue is occurring, in simple terms a patient would
understand. Use everyday body references (e.g., "inner side of your knee"
instead of "medial compartment").

Do NOT mention cause or treatment — only explain WHERE this is happening and
why that area matters.

Clinical text: {clinical_input}

Respond with only the plain-language explanation of the location, nothing else."""

TREATMENT_PROMPT = """Based on the following clinical text, explain THE GOAL AND
POTENTIAL TREATMENT — what typically happens next for this kind of finding, in
reassuring, patient-friendly language. Focus on common treatment goals and
approaches without making specific medical recommendations.

Do NOT mention cause or location — only explain what treatment usually looks like.

Clinical text: {clinical_input}

Respond with only the plain-language explanation of the treatment goal, nothing else."""
