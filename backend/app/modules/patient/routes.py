from datetime import datetime
import os

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Patient, TherapyPlan, User
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
