import json

from app.extensions import db
from app.models import ChatMessage, Gad7Result, Phq9Result, TherapyPlan, Who5Result
from app.services.openrouter_client import chat_completion
from app.services.report_service import generate_therapy_plan_pdf
from app.utils.prompts import THERAPY_PLAN_SYSTEM_PROMPT


def _gather_context(patient) -> dict:
    phq = Phq9Result.query.filter_by(patient_id=patient.id).order_by(Phq9Result.created_at.desc()).first()
    gad = Gad7Result.query.filter_by(patient_id=patient.id).order_by(Gad7Result.created_at.desc()).first()
    who5 = Who5Result.query.filter_by(patient_id=patient.id).order_by(Who5Result.created_at.desc()).first()
    messages = (
        ChatMessage.query.filter_by(patient_id=patient.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(12)
        .all()
    )
    return {
        "name": patient.full_name,
        "age": patient.age,
        "gender": patient.gender,
        "risk_level": patient.latest_risk_level,
        "risk_score": patient.latest_risk_score,
        "phq9": phq.total_score if phq else None,
        "phq9_severity": phq.severity if phq else None,
        "gad7": gad.total_score if gad else None,
        "gad7_severity": gad.severity if gad else None,
        "who5_index": who5.wellbeing_index if who5 else None,
        "who5_raw": who5.raw_score if who5 else None,
        "who5_severity": who5.severity if who5 else None,
        "recent_messages": [
            {"role": m.role.value if hasattr(m.role, "value") else str(m.role), "content": m.content[:300]}
            for m in reversed(messages)
        ],
    }


def _fallback_plan(patient, focus: str = "", language: str = "en") -> dict:
    from app.utils.i18n import normalize_language

    lang = normalize_language(language)
    if lang == "ur":
        base_goals = [
            "Har din ek baar apne feelings check karein",
            "Roz ek chhota self-care ka kaam karein",
            "Is hafte kisi trusted shakhs se rabta karein",
        ]
        base_tasks = [
            "Roz 10 minute walk karein",
            "Is hafte 3 journal entries likhein",
            "Din mein do baar breathing exercise karein",
        ]
        base_behavior = [
            "Sone aur uthne ka fixed time rakhein",
            "Sone se 30 minute pehle screen band karein",
            "Ghabrahat par 5-4-3-2-1 grounding technique use karein",
        ]
        summary = (
            f"Is hafte, {patient.full_name.split()[0]}, aaram se chhote steps par focus karein. "
            "Chhote consistent actions aap ki wellbeing mein madad kar sakte hain."
        )
    else:
        base_goals = [
            "Check in with your feelings once each day",
            "Complete one small self-care activity daily",
            "Reach out to someone you trust this week",
        ]
        base_tasks = [
            "Walk 10 minutes daily",
            "Write 3 journal entries this week",
            "Practice breathing exercise twice daily",
        ]
        base_behavior = [
            "Set a consistent sleep and wake time",
            "Limit screen time 30 minutes before bed",
            "Use the 5-4-3-2-1 grounding technique when anxious",
        ]
        summary = (
            f"This week, {patient.full_name.split()[0]}, focus on gentle, achievable steps. "
            "Small consistent actions can support your wellbeing."
        )
    if focus:
        base_goals[0] = f"{'Focus' if lang == 'en' else 'Focus'}: {focus[:80]}"
    return {
        "weekly_goals": base_goals,
        "coping_tasks": base_tasks,
        "behavioral_suggestions": base_behavior,
        "summary": summary,
    }


def generate_therapy_plan(patient, focus: str = "", language: str = "en") -> TherapyPlan:
    from app.utils.i18n import language_instruction, normalize_language

    lang = normalize_language(language)
    ctx = _gather_context(patient)
    lang_note = "Roman Urdu (Latin script)" if lang == "ur" else "English"
    who5_line = (
        f"{ctx['who5_index']}% wellbeing (raw {ctx['who5_raw']}/25, {ctx['who5_severity']})"
        if ctx["who5_index"] is not None
        else "not completed"
    )
    user_prompt = (
        f"Patient: {ctx['name']}, age {ctx.get('age') or 'unknown'}, gender {ctx.get('gender') or 'unknown'}\n"
        f"Risk: {ctx['risk_level']} (score {ctx['risk_score']})\n"
        f"PHQ-9: {ctx['phq9'] or 'N/A'} ({ctx['phq9_severity'] or 'N/A'}), "
        f"GAD-7: {ctx['gad7'] or 'N/A'} ({ctx['gad7_severity'] or 'N/A'}), "
        f"WHO-5: {who5_line}\n"
        f"Recent conversation snippets:\n"
        + "\n".join(f"- {m['role']}: {m['content'][:120]}" for m in ctx["recent_messages"][-6:])
        + (f"\nPatient focus request: {focus}" if focus else "")
        + f"\n\nWrite ALL plan text in {lang_note}."
        + "\n\nReturn ONLY valid JSON with keys: weekly_goals (3 items), coping_tasks (3-4 items), "
        "behavioral_suggestions (3-4 items), summary (1-2 sentences). "
        "Use concrete actionable items."
    )
    system = THERAPY_PLAN_SYSTEM_PROMPT + f"\n{language_instruction(lang)}"
    try:
        raw = chat_completion([
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ])
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        plan_data = json.loads(text)
    except (json.JSONDecodeError, RuntimeError, Exception):
        plan_data = _fallback_plan(patient, focus, lang)

    for key in ("weekly_goals", "coping_tasks", "behavioral_suggestions"):
        if not isinstance(plan_data.get(key), list) or not plan_data[key]:
            fallback = _fallback_plan(patient, focus, lang)
            plan_data[key] = fallback[key]

    plan = TherapyPlan(
        patient_id=patient.id,
        weekly_goals=plan_data["weekly_goals"][:5],
        coping_tasks=plan_data["coping_tasks"][:6],
        behavioral_suggestions=plan_data["behavioral_suggestions"][:6],
        summary=plan_data.get("summary", ""),
        ai_generated=True,
    )
    db.session.add(plan)
    db.session.flush()

    try:
        pdf_path = generate_therapy_plan_pdf(patient, plan)
        plan.pdf_path = pdf_path
    except Exception:
        plan.pdf_path = None

    db.session.commit()
    return plan


def plan_to_dict(plan: TherapyPlan) -> dict:
    return {
        "id": plan.id,
        "weekly_goals": plan.weekly_goals,
        "coping_tasks": plan.coping_tasks,
        "behavioral_suggestions": plan.behavioral_suggestions,
        "summary": plan.summary,
        "ai_generated": plan.ai_generated,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "has_pdf": bool(plan.pdf_path),
    }
