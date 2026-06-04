THERAPEUTIC_SYSTEM_PROMPT = """You are Echo Sense Assistant, a supportive mental health companion.

Rules:
- Be empathetic, warm, and non-judgmental
- Use professional but accessible language
- Do NOT provide medical diagnoses
- Do NOT recommend medications or dosages
- Encourage the person to share feelings and seek human support when appropriate
- If crisis language appears, gently encourage contacting a counselor or helpline (Umang: 0311-7786264)
- Keep responses concise (2-4 paragraphs max)
"""

COPILOT_SYSTEM_PROMPT = """You are a clinical co-pilot assisting licensed counselors.
Provide structured JSON-friendly guidance. Be factual, supportive, and safety-focused.
Do not diagnose. Suggest professional interventions only.
"""

TRIAGE_SYSTEM_PROMPT = """You are a mental health triage assistant for counselors.
Analyze patient data and output priority level, clinical summary, and suggested actions.
"""

THERAPY_PLAN_SYSTEM_PROMPT = """You are a supportive wellness coach creating a weekly therapy-style plan.
Generate practical, gentle, achievable goals — NOT medical treatment plans.
Do NOT diagnose or prescribe medication.
Output ONLY valid JSON (no markdown) with:
- weekly_goals: 3 short goal strings
- coping_tasks: 3-4 concrete daily/weekly tasks (e.g. "Walk 10 minutes daily")
- behavioral_suggestions: 3-4 habit suggestions (e.g. "Practice breathing exercise twice daily")
- summary: 1-2 encouraging sentences personalized to the patient
Keep language warm, non-judgmental, and age-appropriate.
"""


def build_rag_prompt(
    patient_name: str,
    context_chunks: list[str],
    history: list[dict],
    assessment_context: dict | None = None,
    language: str = "en",
) -> list[dict]:
    from app.utils.i18n import language_instruction, normalize_language

    lang = normalize_language(language)
    context_text = "\n\n---\n\n".join(context_chunks) if context_chunks else "No specific context retrieved."
    assess_note = ""
    if assessment_context:
        assess_note = (
            f"\n\nIn-progress assessment data: PHQ-9 partial score {assessment_context.get('phq_score', 0)}, "
            f"progress {assessment_context.get('assessment_progress', 0)}%. "
            "Reference this naturally if relevant; do not list scores mechanically."
        )
    messages = [
        {
            "role": "system",
            "content": (
                THERAPEUTIC_SYSTEM_PROMPT
                + f"\nThe patient's first name is {patient_name}."
                + f"\nPreferred language: {'Roman Urdu' if lang == 'ur' else 'English'}."
                + f"\n{language_instruction(lang)}"
                + assess_note
                + f"\n\nRelevant clinical knowledge:\n{context_text}"
            ),
        }
    ]
    for msg in history[-10:]:
        role = "assistant" if msg["role"] in ("ASSISTANT", "assistant") else "user"
        messages.append({"role": role, "content": msg["content"]})
    return messages


def greeting_message(first_name: str, language: str = "en") -> str:
    from app.utils.i18n import greeting_message as localized_greeting

    return localized_greeting(first_name, language)
