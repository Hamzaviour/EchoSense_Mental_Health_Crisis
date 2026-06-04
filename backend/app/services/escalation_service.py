from app.extensions import db
from app.models import ChatMessage, Counselor, Escalation, Gad7Result, Notification, PdfReport, Phq9Result, Who5Result
from app.models.chat import MessageRole
from app.models.patient import WorkflowStatus
from app.services.report_service import generate_emergency_pdf


def _conversation_summary(patient_id: int, limit: int = 20) -> str:
    msgs = (
        ChatMessage.query.filter_by(patient_id=patient_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    lines = []
    for m in reversed(msgs):
        lines.append(f"[{m.role.value}] {m.content[:200]}")
    return "\n".join(lines) if lines else "No messages recorded."


def handle_critical_escalation(patient, risk_analysis) -> Escalation:
    escalation = Escalation(
        patient_id=patient.id,
        risk_score=risk_analysis.risk_score,
        risk_level=risk_analysis.risk_level,
        status="OPEN",
    )
    db.session.add(escalation)
    db.session.flush()
    patient.workflow_status = WorkflowStatus.ESCALATED.value

    phq = Phq9Result.query.filter_by(patient_id=patient.id).order_by(Phq9Result.created_at.desc()).first()
    gad = Gad7Result.query.filter_by(patient_id=patient.id).order_by(Gad7Result.created_at.desc()).first()
    who5 = Who5Result.query.filter_by(patient_id=patient.id).order_by(Who5Result.created_at.desc()).first()
    assessments = {
        "phq9": f"{phq.total_score} ({phq.severity})" if phq else "N/A",
        "gad7": f"{gad.total_score} ({gad.severity})" if gad else "N/A",
        "who5": f"{who5.wellbeing_index} ({who5.severity})" if who5 else "N/A",
    }
    summary = _conversation_summary(patient.id)
    filepath = generate_emergency_pdf(patient, escalation, risk_analysis, assessments, summary)

    pdf = PdfReport(
        patient_id=patient.id,
        escalation_id=escalation.id,
        report_type="EMERGENCY",
        file_path=filepath,
    )
    db.session.add(pdf)

    try:
        from app.services.kafka_service import publish_event
        from app.services.notification_service import notify_critical_case
        from app.services.socket_service import emit_queue_update

        notify_critical_case(patient, risk_analysis.risk_score)
        publish_event(
            "emergency_alerts",
            {"patient_id": patient.id, "risk_score": risk_analysis.risk_score},
            key=patient.patient_id,
        )
        emit_queue_update()
    except Exception:
        pass

    return escalation
