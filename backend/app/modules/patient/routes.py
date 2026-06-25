from datetime import datetime
import os

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import (
    Counselor,
    JournalEntry,
    JournalEntryType,
    Patient,
    SessionRequest,
    SessionRequestStatus,
    SessionRequestType,
    TherapyPlan,
    User,
)
from app.services.deepgram_service import transcribe_audio
from app.services.journal_service import analyze_journal_entry, journal_entry_to_dict
from app.services.report_service import generate_journal_export_pdf
from app.services.notification_service import notify_session_request
from app.services.therapy_plan_service import generate_therapy_plan, plan_to_dict
from app.utils.helpers import audit_log

patient_bp = Blueprint("patient", __name__, url_prefix="/api/patient")


def _get_patient():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.patient:
        return None
    return user.patient


@patient_bp.get("/profile")
@jwt_required()
def profile():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404
    return jsonify({
        "id": patient.id,
        "patient_id": patient.patient_id,
        "full_name": patient.full_name,
        "phone": patient.phone,
        "age": patient.age,
        "gender": patient.gender,
        "status": patient.status.value if patient.status else "ACTIVE",
        "consent_given": patient.consent_given,
        "privacy_accepted": patient.privacy_accepted,
        "latest_risk_score": patient.latest_risk_score,
        "latest_risk_level": patient.latest_risk_level,
        "ai_active": patient.ai_active is not False,
        "counselor_active": patient.ai_active is False,
    })


@patient_bp.patch("/profile")
@jwt_required()
def update_profile():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    for field in ("phone", "age", "gender"):
        if field in data:
            setattr(patient, field, data[field])
    db.session.commit()
    return jsonify({"message": "Profile updated"})


@patient_bp.post("/consent")
@jwt_required()
def consent():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    if not data.get("consent") or not data.get("privacy_accepted"):
        return jsonify({"error": "Both consent and privacy acceptance required"}), 400
    patient.consent_given = True
    patient.privacy_accepted = True
    patient.consent_at = datetime.utcnow()
    audit_log(patient.user_id, "CONSENT", "patient")
    db.session.commit()
    return jsonify({"message": "Consent recorded", "consent_given": True})


@patient_bp.get("/therapy-plan")
@jwt_required()
def get_therapy_plan():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    plan = (
        TherapyPlan.query.filter_by(patient_id=patient.id)
        .order_by(TherapyPlan.created_at.desc())
        .first()
    )
    if not plan:
        return jsonify({"plan": None})
    return jsonify({"plan": plan_to_dict(plan)})


@patient_bp.post("/therapy-plan/generate")
@jwt_required()
def create_therapy_plan():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    if not patient.consent_given:
        return jsonify({"error": "Consent required before generating a plan"}), 403
    data = request.get_json() or {}
    focus = (data.get("focus") or "").strip()
    try:
        plan = generate_therapy_plan(patient, focus=focus, language=data.get("language", "en"))
    except Exception as e:
        return jsonify({"error": f"Could not generate plan: {str(e)[:200]}"}), 500
    audit_log(patient.user_id, "THERAPY_PLAN_GENERATE", "therapy_plan", {"plan_id": plan.id})
    return jsonify({"plan": plan_to_dict(plan)}), 201


@patient_bp.get("/therapy-plan/pdf")
@jwt_required()
def download_therapy_plan_pdf():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    plan = (
        TherapyPlan.query.filter_by(patient_id=patient.id)
        .order_by(TherapyPlan.created_at.desc())
        .first()
    )
    if not plan or not plan.pdf_path or not os.path.isfile(plan.pdf_path):
        return jsonify({"error": "No therapy plan PDF available. Generate a plan first."}), 404
    return send_file(
        plan.pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"therapy_plan_{patient.patient_id}.pdf",
    )


# --- Journal ---


@patient_bp.get("/journal")
@jwt_required()
def list_journal_entries():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    if not patient.consent_given:
        return jsonify({"error": "Consent required", "code": "CONSENT_REQUIRED"}), 403
    limit = request.args.get("limit", 30, type=int)
    entries = (
        JournalEntry.query.filter_by(patient_id=patient.id)
        .order_by(JournalEntry.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return jsonify({"entries": [journal_entry_to_dict(e) for e in entries]})


@patient_bp.get("/journal/<int:entry_id>")
@jwt_required()
def get_journal_entry(entry_id: int):
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    entry = JournalEntry.query.filter_by(id=entry_id, patient_id=patient.id).first()
    if not entry:
        return jsonify({"error": "Entry not found"}), 404
    return jsonify({"entry": journal_entry_to_dict(entry)})


@patient_bp.post("/journal")
@jwt_required()
def create_journal_entry():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    if not patient.consent_given:
        return jsonify({"error": "Consent required", "code": "CONSENT_REQUIRED"}), 403
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if len(content) < 10:
        return jsonify({"error": "Please write at least a few words in your reflection"}), 400
    analysis = analyze_journal_entry(content)
    entry = JournalEntry(
        patient_id=patient.id,
        entry_type=JournalEntryType.TEXT,
        content=content,
        ai_summary=analysis["summary"],
        emotions=analysis["emotions"],
        coping_strategies=analysis["coping_strategies"],
    )
    db.session.add(entry)
    patient.last_activity_at = datetime.utcnow()
    audit_log(patient.user_id, "JOURNAL_CREATE", "journal", {"entry_id": entry.id})
    db.session.commit()
    return jsonify({"entry": journal_entry_to_dict(entry)}), 201


@patient_bp.get("/journal/export/pdf")
@jwt_required()
def export_journal_pdf():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    if not patient.consent_given:
        return jsonify({"error": "Consent required", "code": "CONSENT_REQUIRED"}), 403
    entry_id = request.args.get("entry_id", type=int)
    if entry_id:
        entry = JournalEntry.query.filter_by(id=entry_id, patient_id=patient.id).first()
        if not entry:
            return jsonify({"error": "Entry not found"}), 404
        entries = [journal_entry_to_dict(entry)]
    else:
        limit = request.args.get("limit", 20, type=int)
        rows = (
            JournalEntry.query.filter_by(patient_id=patient.id)
            .order_by(JournalEntry.created_at.desc())
            .limit(min(limit, 50))
            .all()
        )
        entries = [journal_entry_to_dict(e) for e in rows]
    try:
        filepath = generate_journal_export_pdf(patient, entries)
    except Exception as e:
        return jsonify({"error": f"PDF export failed: {str(e)[:200]}"}), 500
    audit_log(patient.user_id, "JOURNAL_EXPORT_PDF", "journal", {"count": len(entries)})
    return send_file(
        filepath,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"journal_{patient.patient_id}.pdf",
    )


@patient_bp.post("/journal/voice")
@jwt_required()
def create_voice_journal_entry():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    if not patient.consent_given:
        return jsonify({"error": "Consent required", "code": "CONSENT_REQUIRED"}), 403
    if "audio" not in request.files:
        return jsonify({"error": "Audio file required"}), 400
    f = request.files["audio"]
    try:
        transcript = transcribe_audio(f.read(), f.mimetype or "audio/webm")
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)[:200]}"}), 500
    if not transcript or len(transcript.strip()) < 5:
        return jsonify({"error": "No speech detected. Please try recording again."}), 400
    transcript = transcript.strip()
    analysis = analyze_journal_entry(transcript)
    entry = JournalEntry(
        patient_id=patient.id,
        entry_type=JournalEntryType.VOICE,
        content=transcript,
        transcript=transcript,
        ai_summary=analysis["summary"],
        emotions=analysis["emotions"],
        coping_strategies=analysis["coping_strategies"],
    )
    db.session.add(entry)
    patient.last_activity_at = datetime.utcnow()
    audit_log(patient.user_id, "JOURNAL_VOICE", "journal")
    db.session.commit()
    return jsonify({"entry": journal_entry_to_dict(entry), "transcript": transcript}), 201


# --- Session requests ---


@patient_bp.get("/counselors")
@jwt_required()
def list_counselors_for_patient():
    if not _get_patient():
        return jsonify({"error": "Not found"}), 404
    counselors = Counselor.query.order_by(Counselor.full_name.asc()).all()
    return jsonify({
        "counselors": [
            {
                "id": c.id,
                "counselor_id": c.counselor_id,
                "full_name": c.full_name,
                "specialization": c.specialization or "Mental health counseling",
                "is_on_duty": c.is_on_duty is not False,
            }
            for c in counselors
        ]
    })


def _session_request_to_dict(req: SessionRequest) -> dict:
    counselor_name = req.counselor.full_name if req.counselor else None
    return {
        "id": req.id,
        "request_type": req.request_type.value if req.request_type else None,
        "status": req.status.value if req.status else None,
        "message": req.message,
        "preferred_contact": req.preferred_contact,
        "counselor_id": req.counselor_id,
        "counselor_name": counselor_name,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "updated_at": req.updated_at.isoformat() if req.updated_at else None,
    }


@patient_bp.get("/session-requests")
@jwt_required()
def list_session_requests():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    reqs = (
        SessionRequest.query.filter_by(patient_id=patient.id)
        .order_by(SessionRequest.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify({"requests": [_session_request_to_dict(r) for r in reqs]})


@patient_bp.post("/session-requests")
@jwt_required()
def create_session_request():
    patient = _get_patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    if not patient.consent_given:
        return jsonify({"error": "Consent required", "code": "CONSENT_REQUIRED"}), 403
    data = request.get_json() or {}
    req_type = (data.get("request_type") or "").upper()
    if req_type not in ("CALLBACK", "CHAT_SESSION"):
        return jsonify({"error": "request_type must be CALLBACK or CHAT_SESSION"}), 400
    counselor_id = data.get("counselor_id")
    counselor = None
    if counselor_id:
        counselor = Counselor.query.get(int(counselor_id))
        if not counselor:
            return jsonify({"error": "Counselor not found"}), 404
    pending = SessionRequest.query.filter_by(
        patient_id=patient.id,
        status=SessionRequestStatus.PENDING,
        request_type=SessionRequestType[req_type],
    ).first()
    if pending:
        return jsonify({
            "error": "You already have a pending request of this type",
            "request": _session_request_to_dict(pending),
        }), 409
    req = SessionRequest(
        patient_id=patient.id,
        counselor_id=counselor.id if counselor else None,
        request_type=SessionRequestType[req_type],
        message=(data.get("message") or "").strip() or None,
        preferred_contact=(data.get("preferred_contact") or patient.phone or "").strip() or None,
        status=SessionRequestStatus.PENDING,
    )
    db.session.add(req)
    patient.last_activity_at = datetime.utcnow()
    notify_session_request(patient, req_type, counselor.id if counselor else None)
    audit_log(patient.user_id, "SESSION_REQUEST", "session_request", {"type": req_type})
    db.session.commit()
    return jsonify({"request": _session_request_to_dict(req)}), 201
