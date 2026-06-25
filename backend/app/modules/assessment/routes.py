from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Assessment, Gad7Result, Patient, Phq9Result, User, Who5Result
from app.models.assessment_session import AssessmentSession, SessionStatus
from app.services.assessment_session_service import (
    accept_session,
    decline_session,
    get_active_session,
    get_session_state,
    save_answer,
)
from app.services.socket_service import broadcast_patient_update

assessment_bp = Blueprint("assessment", __name__, url_prefix="/api/assessments")


def _patient():
    user = User.query.get(int(get_jwt_identity()))
    return user.patient if user else None


def _phq_severity(score: int) -> str:
    if score <= 4:
        return "Minimal"
    if score <= 9:
        return "Mild"
    if score <= 14:
        return "Moderate"
    if score <= 19:
        return "Moderately Severe"
    return "Severe"


def _gad_severity(score: int) -> str:
    if score <= 4:
        return "Minimal"
    if score <= 9:
        return "Mild"
    if score <= 14:
        return "Moderate"
    return "Severe"


def _who5_severity(raw: int) -> tuple[float, str]:
    index = raw * 4
    if index >= 50:
        return index, "Good wellbeing"
    if index >= 28:
        return index, "Moderate wellbeing"
    return index, "Poor wellbeing"


@assessment_bp.get("/sessions/active")
@jwt_required()
def active_session():
    patient = _patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    session = get_active_session(patient.id)
    if not session or session.status == SessionStatus.DECLINED:
        return jsonify({"session": None})
    if session.status == SessionStatus.OFFERED:
        return jsonify({
            "session": {
                "session_id": session.id,
                "status": session.status.value,
                "assessment_types": session.assessment_types,
            }
        })
    return jsonify({"session": get_session_state(session)})


@assessment_bp.post("/sessions/<int:session_id>/accept")
@jwt_required()
def accept(session_id: int):
    patient = _patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    session = AssessmentSession.query.filter_by(id=session_id, patient_id=patient.id).first_or_404()
    accept_session(session)
    db.session.commit()
    broadcast_patient_update(patient.id, {"event": "assessment_started", "session": get_session_state(session)})
    return jsonify({"session": get_session_state(session)})


@assessment_bp.post("/sessions/<int:session_id>/decline")
@jwt_required()
def decline(session_id: int):
    patient = _patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    session = AssessmentSession.query.filter_by(id=session_id, patient_id=patient.id).first_or_404()
    decline_session(session)
    return jsonify({"message": "Declined"})


@assessment_bp.patch("/sessions/<int:session_id>/answers")
@jwt_required()
def auto_save_answer(session_id: int):
    patient = _patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    session = AssessmentSession.query.filter_by(
        id=session_id, patient_id=patient.id, status=SessionStatus.IN_PROGRESS
    ).first_or_404()
    data = request.get_json() or {}
    question_id = data.get("question_id")
    value = data.get("value")
    if question_id is None or value is None:
        return jsonify({"error": "question_id and value required"}), 400

    state = save_answer(session, int(question_id), int(value))
    db.session.commit()

    from app.services.assessment_session_service import (
        assessment_completion_summary,
        get_assessment_context_for_rag,
    )

    completion = None
    if state.get("is_complete"):
        completion = assessment_completion_summary(
            patient.id, state.get("assessment_types") or []
        )

    broadcast_patient_update(
        patient.id,
        {
            "event": "assessment_progress",
            "session": state,
            "assessment_context": get_assessment_context_for_rag(patient.id),
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "risk_score": patient.latest_risk_score,
            "risk_level": patient.latest_risk_level,
        },
    )
    return jsonify({"session": state, "summary": completion})


@assessment_bp.post("/sessions/self-start")
@jwt_required()
def self_start_session():
    """Patient-initiated assessment from sidebar (no chat prompt required)."""
    patient = _patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json() or {}
    types = data.get("types") or ["PHQ9", "GAD7", "WHO5"]
    types = [t.upper() for t in types if t.upper() in ("PHQ9", "GAD7", "WHO5")]
    if not types:
        return jsonify({"error": "No valid assessment types provided"}), 400

    from app.services.assessment_session_service import (
        accept_session,
        create_offered_session,
        get_session_state,
    )

    session = create_offered_session(patient.id, types)
    accept_session(session)
    db.session.commit()
    broadcast_patient_update(
        patient.id,
        {"event": "assessment_started", "session": get_session_state(session)},
    )
    return jsonify({"session": get_session_state(session)})


@assessment_bp.get("/<assessment_type>")
@jwt_required()
def get_questions(assessment_type: str):
    atype = assessment_type.upper()
    if atype not in ("PHQ9", "GAD7", "WHO5"):
        return jsonify({"error": "Invalid assessment type"}), 400
    questions = (
        Assessment.query.filter_by(assessment_type=atype)
        .order_by(Assessment.question_number.asc())
        .all()
    )
    prefix = "Over the last 2 weeks, how often have you " if atype in ("PHQ9", "GAD7") else ""
    return jsonify({
        "type": atype,
        "questions": [
            {
                "id": q.id,
                "number": q.question_number,
                "text": f"{prefix}{q.question_text.rstrip('?')}?",
                "options": q.options,
            }
            for q in questions
        ],
    })


@assessment_bp.post("/<assessment_type>/submit")
@jwt_required()
def submit(assessment_type: str):
    """Legacy bulk submit — prefer sidebar auto-save."""
    patient = _patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    atype = assessment_type.upper()
    data = request.get_json() or {}
    responses = data.get("responses") or []
    if not responses:
        return jsonify({"error": "Responses required"}), 400
    total = sum(int(r.get("value", 0)) for r in responses)
    if atype == "PHQ9":
        severity = _phq_severity(total)
        db.session.add(Phq9Result(
            patient_id=patient.id, total_score=total, severity=severity, responses=responses
        ))
        db.session.commit()
        return jsonify({"type": "PHQ9", "total_score": total, "severity": severity})
    if atype == "GAD7":
        severity = _gad_severity(total)
        db.session.add(Gad7Result(
            patient_id=patient.id, total_score=total, severity=severity, responses=responses
        ))
        db.session.commit()
        return jsonify({"type": "GAD7", "total_score": total, "severity": severity})
    if atype == "WHO5":
        wellbeing, severity = _who5_severity(total)
        db.session.add(Who5Result(
            patient_id=patient.id, raw_score=total, wellbeing_index=wellbeing,
            severity=severity, responses=responses,
        ))
        db.session.commit()
        return jsonify({"type": "WHO5", "raw_score": total, "wellbeing_index": wellbeing, "severity": severity})
    return jsonify({"error": "Invalid type"}), 400
