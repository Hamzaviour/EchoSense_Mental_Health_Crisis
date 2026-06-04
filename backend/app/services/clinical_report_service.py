"""Clinical case report generation with AI summaries."""

import json
from collections import Counter
from datetime import datetime

from app.extensions import db
from app.models import (
    ChatMessage,
    Escalation,
    Gad7Result,
    Patient,
    PatientClinicalRecord,
    Phq9Result,
    RiskAnalysis,
    SentimentAnalysis,
    Who5Result,
)
from app.services.chroma_service import retrieve_context, retrieve_patient_memory
from app.services.openrouter_client import chat_completion
from app.services.report_service import generate_clinical_case_report_pdf
from app.utils.keywords import (
    ANXIETY_KEYWORDS,
    DEPRESSION_KEYWORDS,
    SELF_HARM_KEYWORDS,
    SUICIDE_KEYWORDS,
)
from app.utils.prompts import COPILOT_SYSTEM_PROMPT


def _detect_triggers(patient_id: int, limit: int = 40) -> list[str]:
    msgs = (
        ChatMessage.query.filter_by(patient_id=patient_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    found = set()
    all_kw = SUICIDE_KEYWORDS + SELF_HARM_KEYWORDS + DEPRESSION_KEYWORDS + ANXIETY_KEYWORDS
    for m in msgs:
        lower = m.content.lower()
        for kw in all_kw:
            if kw in lower:
                found.add(kw)
    return sorted(found)[:12]


def _sentiment_stats(patient_id: int) -> dict:
    rows = (
        SentimentAnalysis.query.filter_by(patient_id=patient_id)
        .order_by(SentimentAnalysis.created_at.desc())
        .limit(50)
        .all()
    )
    if not rows:
        return {"average": None, "distribution": {}, "trend_note": "Insufficient sentiment data."}

    scores = [r.sentiment_score for r in rows if r.sentiment_score is not None]
    labels = [r.sentiment_label or "neutral" for r in rows]
    label_counts = Counter(lbl.lower() for lbl in labels)
    total = sum(label_counts.values()) or 1
    distribution = {k: round(v / total * 100, 1) for k, v in label_counts.items()}

    avg = sum(scores) / len(scores) if scores else None
    trend_note = "Stable emotional tone."
    if len(scores) >= 4:
        recent = sum(scores[: len(scores) // 2]) / max(1, len(scores) // 2)
        older = sum(scores[len(scores) // 2 :]) / max(1, len(scores) - len(scores) // 2)
        if recent < older - 0.08:
            trend_note = "Sentiment trend declining over recent messages."
        elif recent > older + 0.08:
            trend_note = "Sentiment trend improving over recent messages."

    return {
        "average": round(avg, 3) if avg is not None else None,
        "distribution": distribution,
        "trend_note": trend_note,
        "samples": len(rows),
    }


def _ai_conversation_summary(patient: Patient) -> str:
    msgs = (
        ChatMessage.query.filter_by(patient_id=patient.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(30)
        .all()
    )
    if not msgs:
        return "No conversation history available for summarization."

    history = "\n".join(f"[{m.role.value}] {m.content[:200]}" for m in msgs[-20:])
    query = msgs[-1].content[:120] if msgs else patient.full_name
    try:
        ctx_docs, _ = retrieve_context(query)
        mem = retrieve_patient_memory(patient.patient_id, query)
        chunks = ctx_docs + mem
        context = "\n".join(chunks[:4]) if chunks else ""
    except Exception:
        context = ""

    try:
        raw = chat_completion([
            {
                "role": "system",
                "content": (
                    "Summarize the patient's mental health conversation in 2-4 professional sentences. "
                    "Do not quote verbatim. Focus on themes, emotional tone, and progression."
                ),
            },
            {
                "role": "user",
                "content": f"Patient: {patient.full_name}\nContext:\n{context}\n\nMessages:\n{history}",
            },
        ])
        return raw.strip()[:900]
    except Exception:
        return (
            f"Patient {patient.full_name} has engaged in {len(msgs)} messages. "
            "Reports include stress-related themes requiring continued monitoring and supportive counseling."
        )


def _ai_clinical_summary(patient: Patient, conversation_summary: str) -> str:
    risk = (
        RiskAnalysis.query.filter_by(patient_id=patient.id)
        .order_by(RiskAnalysis.created_at.desc())
        .first()
    )
    phq = Phq9Result.query.filter_by(patient_id=patient.id).order_by(Phq9Result.created_at.desc()).first()
    gad = Gad7Result.query.filter_by(patient_id=patient.id).order_by(Gad7Result.created_at.desc()).first()
    try:
        raw = chat_completion([
            {"role": "system", "content": COPILOT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Patient: {patient.full_name}, Risk: {patient.latest_risk_level} ({patient.latest_risk_score})\n"
                    f"PHQ-9: {phq.total_score if phq else 'N/A'}, GAD-7: {gad.total_score if gad else 'N/A'}\n"
                    f"Conversation summary: {conversation_summary}\n\n"
                    "Write a 2-3 sentence clinical summary for a counselor. No diagnosis."
                ),
            },
        ])
        return raw.strip()[:800]
    except Exception:
        level = (patient.latest_risk_level or "moderate").lower()
        return (
            f"Patient shows {level} risk indicators. "
            "Recommend follow-up counseling and continued monitoring."
        )


def _ai_recommendations(patient: Patient, risk_level: str) -> list[str]:
    try:
        raw = chat_completion([
            {
                "role": "system",
                "content": "Return ONLY JSON: {\"recommendations\": [\"...\", \"...\", \"...\"]}",
            },
            {
                "role": "user",
                "content": (
                    f"Patient risk level: {risk_level}. Suggest 3 therapy/coping recommendations "
                    "(non-medical, actionable)."
                ),
            },
        ])
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        recs = data.get("recommendations", [])
        if recs:
            return recs[:5]
    except Exception:
        pass
    base = [
        "Schedule a follow-up counseling session within one week.",
        "Encourage daily mood journaling and sleep hygiene routines.",
        "Practice grounding and breathing exercises from the coping tools library.",
    ]
    if risk_level in ("High", "Critical"):
        base.append("Consider escalation to helpline if safety concerns persist.")
    return base


def get_or_create_record(patient_id: int) -> PatientClinicalRecord:
    rec = PatientClinicalRecord.query.filter_by(patient_id=patient_id).first()
    if not rec:
        rec = PatientClinicalRecord(patient_id=patient_id)
        db.session.add(rec)
        db.session.commit()
    return rec


def _counselor_notes_for(patient_db_id: int) -> str:
    try:
        rec = PatientClinicalRecord.query.filter_by(patient_id=patient_db_id).first()
        return rec.counselor_notes if rec and rec.counselor_notes else ""
    except Exception:
        db.session.rollback()
        return ""


def build_case_summary(patient_id: int) -> dict:
    """Lightweight summary for Patient Case Navigator sidebar."""
    p = Patient.query.get_or_404(patient_id)
    conv = _ai_conversation_summary(p)
    clinical = _ai_clinical_summary(p, conv)
    sentiment = _sentiment_stats(p.id)
    triggers = _detect_triggers(p.id)
    phq = Phq9Result.query.filter_by(patient_id=p.id).order_by(Phq9Result.created_at.desc()).first()
    gad = Gad7Result.query.filter_by(patient_id=p.id).order_by(Gad7Result.created_at.desc()).first()
    esc = (
        Escalation.query.filter_by(patient_id=p.id)
        .order_by(Escalation.created_at.desc())
        .first()
    )
    counselor_notes = _counselor_notes_for(p.id)
    return {
        "patient_id": p.patient_id,
        "full_name": p.full_name,
        "conversation_summary": conv,
        "ai_clinical_summary": clinical,
        "risk_score": p.latest_risk_score,
        "risk_level": p.latest_risk_level,
        "sentiment_average": sentiment.get("average"),
        "sentiment_distribution": sentiment.get("distribution", {}),
        "sentiment_trend": sentiment.get("trend_note"),
        "trigger_keywords": triggers,
        "assessments": {
            "phq9": {"score": phq.total_score, "severity": phq.severity} if phq else None,
            "gad7": {"score": gad.total_score, "severity": gad.severity} if gad else None,
        },
        "escalation_status": esc.status if esc else None,
        "counselor_notes": counselor_notes,
        "generated_at": datetime.utcnow().isoformat(),
    }


def build_full_report_data(patient_id: int, counselor_notes: str = "") -> dict:
    p = Patient.query.get_or_404(patient_id)
    conv = _ai_conversation_summary(p)
    clinical = _ai_clinical_summary(p, conv)
    sentiment = _sentiment_stats(p.id)
    triggers = _detect_triggers(p.id)
    risk = (
        RiskAnalysis.query.filter_by(patient_id=p.id)
        .order_by(RiskAnalysis.created_at.desc())
        .first()
    )
    phq = Phq9Result.query.filter_by(patient_id=p.id).order_by(Phq9Result.created_at.desc()).first()
    gad = Gad7Result.query.filter_by(patient_id=p.id).order_by(Gad7Result.created_at.desc()).first()
    who5 = Who5Result.query.filter_by(patient_id=p.id).order_by(Who5Result.created_at.desc()).first()
    esc = (
        Escalation.query.filter_by(patient_id=p.id)
        .order_by(Escalation.created_at.desc())
        .first()
    )
    rec = get_or_create_record(p.id)
    notes = counselor_notes.strip() if counselor_notes else (rec.counselor_notes or "")
    recommendations = _ai_recommendations(p, p.latest_risk_level or "Moderate")

    return {
        "identity": {
            "full_name": p.full_name,
            "phone": p.phone or "N/A",
            "age": p.age or "N/A",
            "gender": p.gender or "N/A",
            "patient_id": p.patient_id,
            "registration_date": p.created_at.strftime("%B %d, %Y") if p.created_at else "N/A",
        },
        "conversation_summary": conv,
        "sentiment": sentiment,
        "risk": {
            "score": round(p.latest_risk_score or 0, 1),
            "level": p.latest_risk_level or "Low",
            "trigger_keywords": triggers,
            "escalation_status": esc.status if esc else "None",
            "breakdown": risk.component_breakdown if risk else {},
        },
        "assessments": {
            "phq9": {"score": phq.total_score, "severity": phq.severity} if phq else None,
            "gad7": {"score": gad.total_score, "severity": gad.severity} if gad else None,
            "who5": {"index": who5.wellbeing_index, "severity": who5.severity} if who5 else None,
        },
        "ai_clinical_summary": clinical,
        "counselor_notes": notes or "(No counselor notes recorded.)",
        "recommendations": recommendations,
        "escalation": {
            "sent_to_helpline": bool(esc and esc.helpline_forwarded),
            "timestamp": esc.created_at.isoformat() if esc and esc.created_at else "N/A",
            "action_taken": esc.status if esc else "No escalation on file",
            "helpline_reference": esc.helpline_reference if esc else "N/A",
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


def generate_and_save_report(patient_id: int, counselor_notes: str = "") -> str:
    p = Patient.query.get_or_404(patient_id)
    data = build_full_report_data(patient_id, counselor_notes)
    if counselor_notes.strip():
        rec = get_or_create_record(patient_id)
        rec.counselor_notes = counselor_notes.strip()
        db.session.commit()
    return generate_clinical_case_report_pdf(p, data)
