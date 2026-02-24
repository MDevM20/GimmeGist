"""Prompt templates for the question generation LangGraph nodes."""

SYSTEM_PROMPT = """You are a patient advocacy specialist powered by MedGemma.
Your role is to generate thoughtful, prioritized questions that a patient should
ask their doctor based on clinical reports, health data, and symptoms.

Rules:
- Stay STRICTLY grounded to the provided medical input. Never invent conditions,
  symptoms, or treatments not mentioned or directly implied by the input.
- Generate questions in clear, patient-friendly language (6th-8th grade level).
- Each question should be actionable — something a patient can actually ask.
- Prioritize questions by clinical relevance (most important first).
- Generate 3-5 questions per category.
- Format each question on its own line, prefixed with a number.
- After each question, add a brief (1 sentence) rationale in parentheses
  explaining why this question matters.
"""

UNDERSTANDING_PROMPT = """Based on the following medical information, generate 3-5
prioritized questions a patient should ask their doctor to UNDERSTAND their
condition better. Focus on:
- What the diagnosis/findings mean in everyday terms
- How serious the condition is
- What caused it or what risk factors contributed
- How the condition may progress over time

Medical Report / Clinical Notes:
{medical_input}

Health Data (vitals, metrics, lab results):
{health_data}

Patient-Reported Symptoms:
{symptoms}

Generate only the numbered questions with brief rationales. Do not include any
other text, headers, or explanations."""

TREATMENT_PROMPT = """Based on the following medical information, generate 3-5
prioritized questions a patient should ask their doctor about TREATMENT OPTIONS.
Focus on:
- Available treatment approaches and alternatives
- Benefits and risks of each option
- Timeline for improvement
- What happens if treatment is delayed or skipped

Medical Report / Clinical Notes:
{medical_input}

Health Data (vitals, metrics, lab results):
{health_data}

Patient-Reported Symptoms:
{symptoms}

Generate only the numbered questions with brief rationales. Do not include any
other text, headers, or explanations."""

LIFESTYLE_PROMPT = """Based on the following medical information, generate 3-5
prioritized questions a patient should ask their doctor about LIFESTYLE
MODIFICATIONS. Focus on:
- Activities or movements to avoid or modify
- Diet and nutrition adjustments
- Exercise and physical activity recommendations
- Daily habits that could help or worsen the condition

Medical Report / Clinical Notes:
{medical_input}

Health Data (vitals, metrics, lab results):
{health_data}

Patient-Reported Symptoms:
{symptoms}

Generate only the numbered questions with brief rationales. Do not include any
other text, headers, or explanations."""
