import json
import os
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import (
    ChatMessage,
    Counselor,
    Escalation,
    Gad7Result,
    Notification,
    Patient,
    PdfReport,
    Phq9Result,
    RiskAnalysis,
    SentimentAnalysis,
    SessionRequest,
    SessionRequestStatus,
    User,
    Who5Result,
)
from app.models.assessment_session import SessionStatus
from app.services.assessment_session_service import (
    TYPE_LABELS,
    TYPE_QUESTION_COUNT,
    get_active_session,
)
from app.models.chat import MessageRole
from app.services.openrouter_client import chat_completion
from app.utils.decorators import role_required
from app.utils.prompts import COPILOT_SYSTEM_PROMPT, TRIAGE_SYSTEM_PROMPT

counselor_bp = Blueprint("counselor", __name__, url_prefix="/api/counselor")


def _counselor():
    user = User.query.get(int(get_jwt_identity()))
    return user.counselor if user else None


@counselor_bp.get("/queue")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def queue():
    level = request.args.get("level")
    search = request.args.get("search", "").strip()
    q = Patient.query
    if level:
        q = q.filter(Patient.latest_risk_level == level)
    if search:
        q = q.filter(
            db.or_(
                Patient.full_name.ilike(f"%{search}%"),
                Patient.patient_id.ilike(f"%{search}%"),
            )
        )
    patients = q.order_by(Patient.latest_risk_score.desc()).all()
    result = []
    for p in patients:
        sent = (
            SentimentAnalysis.query.filter_by(patient_id=p.id)
            .order_by(SentimentAnalysis.created_at.desc())
            .first()
        )
        active = get_active_session(p.id)
        assessment_live = None
        if active and active.status == SessionStatus.IN_PROGRESS:
            answered = active.answers.count()
            total = sum(TYPE_QUESTION_COUNT.get(t, 0) for t in active.assessment_types)
            assessment_live = {
                "type": active.current_type,
                "type_label": TYPE_LABELS.get(active.current_type, active.current_type),
                "progress": f"{answered}/{total}",
                "progress_percent": active.progress_percent,
            }
        priority = {"Critical": "Critical", "High": "High", "Moderate": "Moderate"}.get(
            p.latest_risk_level, "Low"
        )
        result.append({
            "id": p.id,
            "patient_id": p.patient_id,
            "full_name": p.full_name,
            "status": p.status.value if p.status else "ACTIVE",
            "latest_risk_score": p.latest_risk_score,
            "latest_risk_level": p.latest_risk_level,
            "sentiment_score": sent.sentiment_score if sent else None,
            "sentiment_label": sent.sentiment_label if sent else None,
            "priority": priority,
            "assessment": assessment_live,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })
    return jsonify({"patients": result})


@counselor_bp.get("/patients/<int:patient_db_id>")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def patient_detail(patient_db_id: int):
    p = Patient.query.get_or_404(patient_db_id)
    messages = (
        ChatMessage.query.filter_by(patient_id=p.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
        .all()
    )
    risks = (
        RiskAnalysis.query.filter_by(patient_id=p.id)
        .order_by(RiskAnalysis.created_at.desc())
        .limit(20)
        .all()
    )
    sentiments = (
        SentimentAnalysis.query.filter_by(patient_id=p.id)
        .order_by(SentimentAnalysis.created_at.desc())
        .limit(20)
        .all()
    )
    phq = Phq9Result.query.filter_by(patient_id=p.id).order_by(Phq9Result.created_at.desc()).first()
    gad = Gad7Result.query.filter_by(patient_id=p.id).order_by(Gad7Result.created_at.desc()).first()
    who5 = Who5Result.query.filter_by(patient_id=p.id).order_by(Who5Result.created_at.desc()).first()
    from app.services.clinical_report_service import get_or_create_record

    rec = get_or_create_record(p.id)
    return jsonify({
        "patient": {
            "id": p.id,
            "patient_id": p.patient_id,
            "full_name": p.full_name,
            "phone": p.phone,
            "age": p.age,
            "gender": p.gender,
            "status": p.status.value if p.status else "ACTIVE",
            "latest_risk_score": p.latest_risk_score,
            "latest_risk_level": p.latest_risk_level,
            "workflow_status": p.workflow_status,
            "follow_up_at": p.follow_up_at.isoformat() if p.follow_up_at else None,
            "session_scheduled_at": p.session_scheduled_at.isoformat() if p.session_scheduled_at else None,
            "counselor_notes": rec.counselor_notes or "",
            "ai_active": p.ai_active is not False,
            "counselor_active": p.ai_active is False,
            "counselor_takeover_at": p.counselor_takeover_at.isoformat() if p.counselor_takeover_at else None,
        },
        "messages": [
            {"id": m.id, "role": m.role.value, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in reversed(messages)
        ],
        "risk_history": [
            {"score": r.risk_score, "level": r.risk_level, "breakdown": r.component_breakdown, "at": r.created_at.isoformat()}
            for r in reversed(risks)
        ],
        "sentiment_trend": [
            {"score": s.sentiment_score, "label": s.sentiment_label, "at": s.created_at.isoformat()}
            for s in reversed(sentiments)
        ],
        "assessments": {
            "phq9": {"score": phq.total_score, "severity": phq.severity} if phq else None,
            "gad7": {"score": gad.total_score, "severity": gad.severity} if gad else None,
            "who5": {"index": who5.wellbeing_index, "severity": who5.severity} if who5 else None,
        },
    })


@counselor_bp.post("/messages")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def send_message():
    data = request.get_json() or {}
    patient_id = data.get("patient_id")
    content = (data.get("content") or "").strip()
    if not patient_id or not content:
        return jsonify({"error": "patient_id and content required"}), 400
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"error": "Patient not found"}), 404
    from app.utils.session_helpers import get_active_session

    session = get_active_session(p)
    msg = ChatMessage(
        session_id=session.id,
        patient_id=p.id,
        role=MessageRole.COUNSELOR,
        content=content,
    )
    db.session.add(msg)
    p.last_activity_at = datetime.utcnow()
    if p.workflow_status in (None, "NEW", "RESOLVED"):
        from app.models.patient import WorkflowStatus

        p.workflow_status = WorkflowStatus.IN_PROGRESS.value
    counselor = _counselor()
    if counselor:
        p.assigned_counselor_id = counselor.id
    db.session.commit()
    from app.services.socket_service import emit_patient_message

    emit_patient_message(
        p.id,
        {
            "id": msg.id,
            "role": "COUNSELOR",
            "content": content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        },
    )
    return jsonify({"message": "Sent", "id": msg.id})


@counselor_bp.post("/copilot")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def copilot():
    data = request.get_json() or {}
    patient_id = data.get("patient_id")
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"error": "Not found"}), 404
    msgs = ChatMessage.query.filter_by(patient_id=p.id).order_by(ChatMessage.created_at.desc()).limit(15).all()
    context = "\n".join(f"[{m.role.value}] {m.content}" for m in reversed(msgs))
    prompt = [
        {"role": "system", "content": COPILOT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Patient: {p.full_name}, Risk: {p.latest_risk_level} ({p.latest_risk_score})\n"
                f"Conversation:\n{context}\n\n"
                "Provide JSON with: summary, risk_factors (list), suggested_messages (3 strings), next_question"
            ),
        },
    ]
    try:
        raw = chat_completion(prompt)
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {
                "summary": raw[:500],
                "risk_factors": [p.latest_risk_level],
                "suggested_messages": [
                    "I hear that you're going through a difficult time.",
                    "Your feelings are valid, and I'm glad you reached out.",
                    "Are you safe right now? Is there someone you can be with?",
                ],
                "next_question": "Can you tell me more about what triggered these feelings?",
            }
    except Exception as e:
        result = {
            "summary": "Unable to generate AI summary.",
            "risk_factors": [p.latest_risk_level],
            "suggested_messages": [
                "Thank you for sharing. I'm here to support you.",
                "It sounds like this has been really hard for you.",
                "Would you like to talk about what support would help most?",
            ],
            "next_question": "What would feel most helpful right now?",
            "error": str(e),
        }
    return jsonify(result)


@counselor_bp.post("/triage")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def triage():
    data = request.get_json() or {}
    patient_id = data.get("patient_id")
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"error": "Not found"}), 404
    risks = RiskAnalysis.query.filter_by(patient_id=p.id).order_by(RiskAnalysis.created_at.desc()).limit(5).all()
    prompt = [
        {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Patient {p.full_name}, ID {p.patient_id}, current risk {p.latest_risk_score} ({p.latest_risk_level}).\n"
                f"Recent risks: {[{'score': r.risk_score, 'level': r.risk_level} for r in risks]}\n"
                "Return JSON: priority_level (1-5), clinical_summary, suggested_actions (list)"
            ),
        },
    ]
    try:
        raw = chat_completion(prompt)
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            priority = 1 if p.latest_risk_level == "Critical" else 3
            result = {
                "priority_level": priority,
                "clinical_summary": raw[:400],
                "suggested_actions": ["Review patient history", "Schedule follow-up", "Monitor risk"],
            }
    except Exception:
        priority_map = {"Critical": 1, "High": 2, "Moderate": 3, "Low": 5}
        result = {
            "priority_level": priority_map.get(p.latest_risk_level, 4),
            "clinical_summary": f"Patient at {p.latest_risk_level} risk level.",
            "suggested_actions": ["Conduct safety check", "Review assessments", "Document session"],
        }
    return jsonify(result)


@counselor_bp.get("/notifications")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def notifications():
    counselor = _counselor()
    q = Notification.query
    if counselor:
        q = q.filter(
            db.or_(Notification.counselor_id == counselor.id, Notification.counselor_id.is_(None))
        )
    notifs = q.order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify({
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.notification_type,
                "notification_type": n.notification_type,
                "is_read": n.is_read,
                "patient_id": n.patient_id,
                "patient_name": Patient.query.get(n.patient_id).full_name if n.patient_id and Patient.query.get(n.patient_id) else None,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifs
        ],
        "unread_count": sum(1 for n in notifs if not n.is_read),
    })


@counselor_bp.patch("/notifications/<int:notif_id>/read")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def mark_read(notif_id: int):
    n = Notification.query.get_or_404(notif_id)
    n.is_read = True
    db.session.commit()
    return jsonify({"message": "Marked read"})


@counselor_bp.get("/triage-board")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def triage_board():
    from app.services.counselor_triage_service import get_triage_board

    workflow = request.args.get("workflow")
    search = request.args.get("search", "").strip()
    return jsonify(get_triage_board(workflow_filter=workflow or None, search=search))


@counselor_bp.patch("/patients/<int:patient_db_id>/workflow")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def update_patient_workflow(patient_db_id: int):
    from app.services.counselor_triage_service import update_workflow

    p = Patient.query.get_or_404(patient_db_id)
    data = request.get_json() or {}
    counselor = _counselor()
    update_workflow(p, data, counselor.id if counselor else None)
    from app.services.counselor_triage_service import build_triage_card

    return jsonify({"patient": build_triage_card(p)})


@counselor_bp.post("/suggested-responses")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def suggested_responses():
    from app.services.counselor_triage_service import generate_suggested_responses

    data = request.get_json() or {}
    p = Patient.query.get(data.get("patient_id"))
    if not p:
        return jsonify({"error": "Not found"}), 404
    tone = data.get("tone", "supportive")
    return jsonify(generate_suggested_responses(p, tone))


@counselor_bp.post("/escalate")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def escalate_patient():
    from app.services.counselor_triage_service import counselor_escalate

    data = request.get_json() or {}
    p = Patient.query.get(data.get("patient_id"))
    if not p:
        return jsonify({"error": "Not found"}), 404
    counselor = _counselor()
    try:
        result = counselor_escalate(p, counselor.id if counselor else None)
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500
    return jsonify(result), 201


@counselor_bp.patch("/escalations/<int:escalation_id>/status")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def update_escalation_status(escalation_id: int):
    data = request.get_json() or {}
    status = data.get("status")
    if status not in ("ACKNOWLEDGED", "RESOLVED"):
        return jsonify({"error": "status must be ACKNOWLEDGED or RESOLVED"}), 400
    esc = Escalation.query.get_or_404(escalation_id)
    esc.status = status
    if status == "ACKNOWLEDGED":
        esc.acknowledged_at = datetime.utcnow()
    elif status == "RESOLVED":
        esc.resolved_at = datetime.utcnow()
        patient = Patient.query.get(esc.patient_id)
        if patient:
            from app.models.patient import WorkflowStatus

            patient.workflow_status = WorkflowStatus.RESOLVED.value
    db.session.commit()
    return jsonify({
        "id": esc.id,
        "status": esc.status,
        "acknowledged_at": esc.acknowledged_at.isoformat() if esc.acknowledged_at else None,
        "resolved_at": esc.resolved_at.isoformat() if esc.resolved_at else None,
    })


@counselor_bp.get("/escalations/active")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def active_escalations():
    from app.models import Patient as P

    rows = (
        Escalation.query.filter(Escalation.status.in_(["SENT", "ACKNOWLEDGED", "OPEN"]))
        .order_by(Escalation.created_at.desc())
        .limit(50)
        .all()
    )
    result = []
    for e in rows:
        p = P.query.get(e.patient_id)
        pdf = PdfReport.query.filter_by(escalation_id=e.id).first()
        result.append({
            "id": e.id,
            "patient_id": e.patient_id,
            "patient_name": p.full_name if p else None,
            "patient_code": p.patient_id if p else None,
            "risk_score": e.risk_score,
            "risk_level": e.risk_level,
            "status": e.status,
            "ai_summary": e.ai_summary,
            "helpline_reference": e.helpline_reference,
            "helpline_forwarded": e.helpline_forwarded,
            "has_pdf": bool(pdf and pdf.file_path),
            "created_at": e.created_at.isoformat(),
            "acknowledged_at": e.acknowledged_at.isoformat() if e.acknowledged_at else None,
        })
    return jsonify({"escalations": result})


@counselor_bp.get("/patients/<int:patient_db_id>/case-summary")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def patient_case_summary(patient_db_id: int):
    from app.extensions import db
    from app.services.clinical_report_service import build_case_summary

    try:
        return jsonify(build_case_summary(patient_db_id))
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Could not build case summary: {str(e)[:200]}"}), 500


@counselor_bp.patch("/patients/<int:patient_db_id>/clinical-notes")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def update_clinical_notes(patient_db_id: int):
    from app.services.clinical_report_service import get_or_create_record

    Patient.query.get_or_404(patient_db_id)
    data = request.get_json() or {}
    notes = (data.get("counselor_notes") or "").strip()
    rec = get_or_create_record(patient_db_id)
    rec.counselor_notes = notes
    counselor = _counselor()
    if counselor:
        rec.updated_by = counselor.id
    db.session.commit()
    return jsonify({"counselor_notes": rec.counselor_notes})


@counselor_bp.post("/patients/<int:patient_db_id>/assessment-report/pdf")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def download_assessment_report_pdf(patient_db_id: int):
    from app.services.report_service import build_assessment_report_data, generate_assessment_report_pdf

    p = Patient.query.get_or_404(patient_db_id)
    data = build_assessment_report_data(p)
    if not any(data.get(k) for k in ("phq9", "gad7", "who5")):
        return jsonify({"error": "No assessment results available for this patient"}), 404
    try:
        filepath = generate_assessment_report_pdf(p, data)
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500
    if not filepath or not os.path.isfile(filepath):
        return jsonify({"error": "PDF generation failed"}), 500
    return send_file(
        filepath,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"assessment_{p.patient_id}.pdf",
    )


@counselor_bp.post("/patients/<int:patient_db_id>/clinical-report/pdf")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def download_clinical_report_pdf(patient_db_id: int):
    from app.services.clinical_report_service import generate_and_save_report

    p = Patient.query.get_or_404(patient_db_id)
    data = request.get_json() or {}
    notes = (data.get("counselor_notes") or "").strip()
    try:
        filepath = generate_and_save_report(patient_db_id, notes)
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500
    if not filepath or not os.path.isfile(filepath):
        return jsonify({"error": "PDF generation failed"}), 500
    return send_file(
        filepath,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"clinical_case_{p.patient_id}.pdf",
    )


@counselor_bp.post("/patients/<int:patient_db_id>/takeover")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def take_over_chat(patient_db_id: int):
    from app.models.chat import MessageRole
    from app.models.patient import WorkflowStatus
    from app.services.notification_service import notify_counselor_mentioned
    from app.services.socket_service import emit_patient_takeover
    from app.utils.session_helpers import get_active_session

    p = Patient.query.get_or_404(patient_db_id)
    counselor = _counselor()
    p.ai_active = False
    p.counselor_takeover_at = datetime.utcnow()
    if counselor:
        p.assigned_counselor_id = counselor.id
    if p.workflow_status in (None, WorkflowStatus.NEW.value, WorkflowStatus.RESOLVED.value):
        p.workflow_status = WorkflowStatus.IN_PROGRESS.value

    session = get_active_session(p)
    system_text = "A counselor has joined the conversation."
    sys_msg = ChatMessage(
        session_id=session.id,
        patient_id=p.id,
        role=MessageRole.SYSTEM,
        content=system_text,
    )
    db.session.add(sys_msg)
    db.session.commit()

    payload = {
        "id": sys_msg.id,
        "role": "SYSTEM",
        "content": system_text,
        "created_at": sys_msg.created_at.isoformat() if sys_msg.created_at else None,
        "counselor_active": True,
        "ai_active": False,
    }
    emit_patient_takeover(p.id, payload)
    counselor_name = counselor.full_name if counselor else "Counselor"
    notify_counselor_mentioned(p, f"{counselor_name} took over live chat")

    return jsonify({
        "message": "Chat takeover active",
        "ai_active": False,
        "counselor_active": True,
        "patient_id": p.id,
    })


@counselor_bp.post("/escalations/<int:escalation_id>/helpline")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def escalate_to_helpline(escalation_id: int):
    from app.services.counselor_triage_service import forward_escalation_to_helpline

    esc = Escalation.query.get_or_404(escalation_id)
    try:
        result = forward_escalation_to_helpline(esc)
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500
    return jsonify(result)


def _counselor_session_request_dict(req: SessionRequest) -> dict:
    return {
        "id": req.id,
        "patient_id": req.patient_id,
        "patient_name": req.patient.full_name if req.patient else None,
        "patient_code": req.patient.patient_id if req.patient else None,
        "request_type": req.request_type.value if req.request_type else None,
        "status": req.status.value if req.status else None,
        "message": req.message,
        "preferred_contact": req.preferred_contact,
        "counselor_id": req.counselor_id,
        "counselor_name": req.counselor.full_name if req.counselor else None,
        "created_at": req.created_at.isoformat() if req.created_at else None,
    }


@counselor_bp.get("/session-requests")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def list_counselor_session_requests():
    counselor = _counselor()
    status = request.args.get("status", "PENDING")
    q = SessionRequest.query
    if status:
        try:
            q = q.filter_by(status=SessionRequestStatus[status.upper()])
        except KeyError:
            pass
    if counselor:
        q = q.filter(
            db.or_(
                SessionRequest.counselor_id.is_(None),
                SessionRequest.counselor_id == counselor.id,
            )
        )
    reqs = q.order_by(SessionRequest.created_at.desc()).limit(100).all()
    return jsonify({"requests": [_counselor_session_request_dict(r) for r in reqs]})


@counselor_bp.patch("/session-requests/<int:request_id>")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def update_session_request(request_id: int):
    req = SessionRequest.query.get_or_404(request_id)
    counselor = _counselor()
    if req.counselor_id and counselor and req.counselor_id != counselor.id:
        return jsonify({"error": "This request is assigned to another counselor"}), 403
    data = request.get_json() or {}
    new_status = (data.get("status") or "").upper()
    if new_status not in ("APPROVED", "DECLINED", "COMPLETED", "PENDING"):
        return jsonify({"error": "Invalid status"}), 400
    req.status = SessionRequestStatus[new_status]
    if counselor and not req.counselor_id:
        req.counselor_id = counselor.id
    if data.get("counselor_notes"):
        req.counselor_notes = (data.get("counselor_notes") or "").strip()
    if new_status == "APPROVED" and req.request_type.value == "CHAT_SESSION":
        patient = req.patient
        if patient and counselor:
            patient.assigned_counselor_id = counselor.id
    req.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"request": _counselor_session_request_dict(req)})
