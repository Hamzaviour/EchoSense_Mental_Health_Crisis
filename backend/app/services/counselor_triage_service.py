import json
from datetime import datetime, timezone

from app.extensions import db
from app.models import (
    ChatMessage,
    Escalation,
    Gad7Result,
    Notification,
    Patient,
    PdfReport,
    Phq9Result,
    RiskAnalysis,
    SentimentAnalysis,
    Who5Result,
)
from app.models.patient import WorkflowStatus
from app.services.helpline_service import forward_to_umang_helpline
from app.services.openrouter_client import chat_completion
from app.services.report_service import generate_emergency_pdf
from app.utils.prompts import COPILOT_SYSTEM_PROMPT


def _time_ago(dt: datetime | None) -> str | None:
    if not dt:
        return None
    now = datetime.utcnow()
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    delta = now - dt
    mins = int(delta.total_seconds() // 60)
    if mins < 1:
        return "Just now"
    if mins < 60:
        return f"{mins}m ago"
    hours = mins // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def _last_message(patient_id: int) -> dict | None:
    msg = (
        ChatMessage.query.filter_by(patient_id=patient_id)
        .order_by(ChatMessage.created_at.desc())
        .first()
    )
    if not msg:
        return None
    return {
        "content": msg.content[:120],
        "role": msg.role.value,
        "at": msg.created_at.isoformat() if msg.created_at else None,
    }


def _assessment_status(patient_id: int) -> dict:
    phq = Phq9Result.query.filter_by(patient_id=patient_id).first()
    gad = Gad7Result.query.filter_by(patient_id=patient_id).first()
    who5 = Who5Result.query.filter_by(patient_id=patient_id).first()
    return {
        "phq9_done": phq is not None,
        "gad7_done": gad is not None,
        "who5_done": who5 is not None,
        "phq9_score": phq.total_score if phq else None,
        "gad7_score": gad.total_score if gad else None,
        "label": _assessment_label(phq, gad),
    }


def _assessment_label(phq, gad) -> str:
    parts = []
    if phq:
        parts.append(f"PHQ-9 ✓ ({phq.total_score})")
    else:
        parts.append("PHQ-9 pending")
    if gad:
        parts.append(f"GAD-7 ✓ ({gad.total_score})")
    else:
        parts.append("GAD-7 pending")
    return " · ".join(parts)


def build_triage_card(patient: Patient) -> dict:
    sent = (
        SentimentAnalysis.query.filter_by(patient_id=patient.id)
        .order_by(SentimentAnalysis.created_at.desc())
        .first()
    )
    activity = patient.last_activity_at or patient.updated_at
    last_msg = _last_message(patient.id)
    if last_msg and last_msg.get("at"):
        try:
            activity = datetime.fromisoformat(last_msg["at"])
        except ValueError:
            pass

    open_esc = (
        Escalation.query.filter_by(patient_id=patient.id)
        .filter(Escalation.status.in_(["SENT", "ACKNOWLEDGED", "OPEN"]))
        .order_by(Escalation.created_at.desc())
        .first()
    )

    return {
        "id": patient.id,
        "patient_id": patient.patient_id,
        "full_name": patient.full_name,
        "latest_risk_score": round(patient.latest_risk_score or 0, 1),
        "latest_risk_level": patient.latest_risk_level or "Low",
        "sentiment_score": round(sent.sentiment_score, 2) if sent else None,
        "sentiment_label": sent.sentiment_label if sent else None,
        "last_message": last_msg,
        "assessment_status": _assessment_status(patient.id),
        "time_since_activity": _time_ago(activity),
        "last_activity_at": activity.isoformat() if activity else None,
        "workflow_status": patient.workflow_status or WorkflowStatus.NEW.value,
        "follow_up_at": patient.follow_up_at.isoformat() if patient.follow_up_at else None,
        "session_scheduled_at": patient.session_scheduled_at.isoformat() if patient.session_scheduled_at else None,
        "escalation_status": open_esc.status if open_esc else None,
        "escalation_id": open_esc.id if open_esc else None,
    }


def get_triage_board(workflow_filter: str | None = None, search: str = "") -> dict:
    q = Patient.query
    if workflow_filter:
        q = q.filter(Patient.workflow_status == workflow_filter)
    if search:
        q = q.filter(
            db.or_(
                Patient.full_name.ilike(f"%{search}%"),
                Patient.patient_id.ilike(f"%{search}%"),
            )
        )
    patients = q.order_by(Patient.latest_risk_score.desc()).all()
    cards = [build_triage_card(p) for p in patients]

    columns = {"Low": [], "Moderate": [], "High": [], "Critical": []}
    for card in cards:
        level = card["latest_risk_level"]
        if level not in columns:
            level = "Low"
        columns[level].append(card)

    workflow_counts = {}
    for ws in WorkflowStatus:
        workflow_counts[ws.value] = Patient.query.filter_by(workflow_status=ws.value).count()

    return {
        "columns": columns,
        "patients": cards,
        "workflow_counts": workflow_counts,
    }


TONE_PROMPTS = {
    "calm": "Use a calm, gentle, grounding tone.",
    "supportive": "Use a warm, empathetic, supportive tone.",
    "firm": "Use a clear, steady, safety-focused tone while remaining compassionate.",
}

FALLBACK_BY_TONE = {
    "calm": [
        "I'm here with you. Can you tell me more about what you're feeling?",
        "Let's take this one step at a time. You're not alone.",
        "It's okay to feel overwhelmed. I'm listening.",
    ],
    "supportive": [
        "You're not alone. Let's talk through this together.",
        "Thank you for reaching out — that takes courage.",
        "I understand this is difficult. I'm here to support you.",
    ],
    "firm": [
        "I want to make sure you're safe. Are you in a safe place right now?",
        "Your safety matters. Please stay with me while we work through this.",
        "I'm taking what you've shared seriously. Let's focus on immediate support.",
    ],
}


def generate_suggested_responses(patient: Patient, tone: str = "supportive") -> dict:
    tone = tone if tone in TONE_PROMPTS else "supportive"
    msgs = (
        ChatMessage.query.filter_by(patient_id=patient.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(12)
        .all()
    )
    context = "\n".join(f"[{m.role.value}] {m.content}" for m in reversed(msgs))
    prompt = [
        {"role": "system", "content": COPILOT_SYSTEM_PROMPT + f" {TONE_PROMPTS[tone]}"},
        {
            "role": "user",
            "content": (
                f"Patient: {patient.full_name}, Risk: {patient.latest_risk_level} ({patient.latest_risk_score})\n"
                f"Conversation:\n{context}\n\n"
                "Return ONLY valid JSON: "
                '{"responses": ["msg1", "msg2", "msg3"], "tone": "' + tone + '"}'
            ),
        },
    ]
    try:
        raw = chat_completion(prompt)
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        responses = data.get("responses", [])[:3]
        if len(responses) < 3:
            raise ValueError("insufficient responses")
    except Exception:
        responses = FALLBACK_BY_TONE[tone]
    return {"tone": tone, "responses": responses}


def _ai_escalation_summary(patient: Patient) -> str:
    msgs = ChatMessage.query.filter_by(patient_id=patient.id).order_by(ChatMessage.created_at.desc()).limit(15).all()
    context = "\n".join(f"[{m.role.value}] {m.content[:150]}" for m in reversed(msgs))
    try:
        raw = chat_completion([
            {"role": "system", "content": "Summarize patient crisis context for helpline handoff in 3-4 sentences."},
            {
                "role": "user",
                "content": f"Patient {patient.full_name}, risk {patient.latest_risk_level}. Messages:\n{context}",
            },
        ])
        return raw[:800]
    except Exception:
        return f"Patient {patient.full_name} escalated at {patient.latest_risk_level} risk level."


def counselor_escalate(patient: Patient, counselor_id: int | None) -> dict:
    risk = (
        RiskAnalysis.query.filter_by(patient_id=patient.id)
        .order_by(RiskAnalysis.created_at.desc())
        .first()
    )
    risk_score = risk.risk_score if risk else patient.latest_risk_score or 0
    risk_level = risk.risk_level if risk else patient.latest_risk_level or "High"

    ai_summary = _ai_escalation_summary(patient)
    escalation = Escalation(
        patient_id=patient.id,
        counselor_id=counselor_id,
        risk_score=risk_score,
        risk_level=risk_level,
        status="SENT",
        ai_summary=ai_summary,
        helpline_forwarded=False,
    )
    db.session.add(escalation)
    db.session.flush()

    phq = Phq9Result.query.filter_by(patient_id=patient.id).order_by(Phq9Result.created_at.desc()).first()
    gad = Gad7Result.query.filter_by(patient_id=patient.id).order_by(Gad7Result.created_at.desc()).first()
    who5 = Who5Result.query.filter_by(patient_id=patient.id).order_by(Who5Result.created_at.desc()).first()
    assessments = {
        "phq9": f"{phq.total_score} ({phq.severity})" if phq else "N/A",
        "gad7": f"{gad.total_score} ({gad.severity})" if gad else "N/A",
        "who5": f"{who5.wellbeing_index} ({who5.severity})" if who5 else "N/A",
    }
    chat_summary = "\n".join(
        f"[{m.role.value}] {m.content[:200]}"
        for m in reversed(
            ChatMessage.query.filter_by(patient_id=patient.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(25)
            .all()
        )
    )
    full_summary = f"{ai_summary}\n\n--- Chat History ---\n{chat_summary}"

    pdf_path = None
    if risk:
        pdf_path = generate_emergency_pdf(patient, escalation, risk, assessments, full_summary)
    db.session.add(
        PdfReport(
            patient_id=patient.id,
            escalation_id=escalation.id,
            report_type="ESCALATION",
            file_path=pdf_path,
        )
    )

    helpline = forward_to_umang_helpline(patient, escalation, pdf_path)
    escalation.helpline_forwarded = True
    escalation.helpline_reference = helpline["reference"]

    patient.workflow_status = WorkflowStatus.ESCALATED.value
    db.session.commit()

    try:
        from app.services.socket_service import broadcast_patient_update, emit_queue_update

        broadcast_patient_update(patient.id, {"event": "escalation", "patient_id": patient.id})
        emit_queue_update()
    except Exception:
        pass

    return {
        "escalation_id": escalation.id,
        "status": escalation.status,
        "helpline_reference": escalation.helpline_reference,
        "helpline": helpline,
        "pdf_available": bool(pdf_path),
        "ai_summary": ai_summary,
    }


def forward_escalation_to_helpline(escalation: Escalation) -> dict:
    """Forward an existing escalation (e.g. auto-critical OPEN) to Umang helpline."""
    if escalation.helpline_forwarded and escalation.helpline_reference:
        return {
            "escalation_id": escalation.id,
            "status": escalation.status,
            "helpline_reference": escalation.helpline_reference,
            "already_sent": True,
        }
    patient = Patient.query.get(escalation.patient_id)
    if not patient:
        raise ValueError("Patient not found")
    pdf = PdfReport.query.filter_by(escalation_id=escalation.id).first()
    pdf_path = pdf.file_path if pdf else None
    helpline = forward_to_umang_helpline(patient, escalation, pdf_path)
    escalation.helpline_forwarded = True
    escalation.helpline_reference = helpline["reference"]
    if escalation.status == "OPEN":
        escalation.status = "SENT"
    patient.workflow_status = WorkflowStatus.ESCALATED.value
    db.session.commit()
    try:
        from app.services.socket_service import emit_queue_update
        emit_queue_update()
    except Exception:
        pass
    return {
        "escalation_id": escalation.id,
        "status": escalation.status,
        "helpline_reference": escalation.helpline_reference,
        "helpline": helpline,
    }


def update_workflow(patient: Patient, data: dict, counselor_id: int | None) -> Patient:
    if "workflow_status" in data:
        patient.workflow_status = data["workflow_status"]
    if "follow_up_at" in data:
        val = data["follow_up_at"]
        patient.follow_up_at = datetime.fromisoformat(val.replace("Z", "")) if val else None
        if val:
            patient.workflow_status = WorkflowStatus.FOLLOW_UP.value
    if "session_scheduled_at" in data:
        val = data["session_scheduled_at"]
        patient.session_scheduled_at = datetime.fromisoformat(val.replace("Z", "")) if val else None
    if counselor_id and data.get("assign_to_me"):
        patient.assigned_counselor_id = counselor_id
    if data.get("workflow_status") == WorkflowStatus.IN_PROGRESS.value and counselor_id:
        patient.assigned_counselor_id = counselor_id
    patient.updated_at = datetime.utcnow()
    db.session.commit()
    return patient
