from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from app.extensions import db
from app.models import Counselor, Escalation, Gad7Result, Patient, Phq9Result, RiskAnalysis, SentimentAnalysis, User
from app.services.admin_service import create_counselor_account, delete_patient_account
from app.utils.decorators import role_required
from app.utils.helpers import audit_log

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/analytics")
@jwt_required()
@role_required("ADMIN", "COUNSELOR")
def analytics():
    since = datetime.utcnow() - timedelta(days=30)
    total_patients = Patient.query.count()
    risk_dist = (
        db.session.query(RiskAnalysis.risk_level, func.count(RiskAnalysis.id))
        .filter(RiskAnalysis.created_at >= since)
        .group_by(RiskAnalysis.risk_level)
        .all()
    )
    sentiment_dist = (
        db.session.query(SentimentAnalysis.sentiment_label, func.count(SentimentAnalysis.id))
        .filter(SentimentAnalysis.created_at >= since)
        .group_by(SentimentAnalysis.sentiment_label)
        .all()
    )
    escalations = Escalation.query.filter(Escalation.created_at >= since).count()
    phq_avg = db.session.query(func.avg(Phq9Result.total_score)).filter(Phq9Result.created_at >= since).scalar()
    gad_avg = db.session.query(func.avg(Gad7Result.total_score)).filter(Gad7Result.created_at >= since).scalar()
    daily_cases = (
        db.session.query(func.date(RiskAnalysis.created_at), func.count(RiskAnalysis.id))
        .filter(RiskAnalysis.created_at >= since)
        .group_by(func.date(RiskAnalysis.created_at))
        .all()
    )
    since_7d = datetime.utcnow() - timedelta(days=7)
    daily_crisis = (
        db.session.query(func.date(RiskAnalysis.created_at), func.count(RiskAnalysis.id))
        .filter(
            RiskAnalysis.created_at >= since_7d,
            RiskAnalysis.risk_level.in_(["Critical", "High"]),
        )
        .group_by(func.date(RiskAnalysis.created_at))
        .order_by(func.date(RiskAnalysis.created_at))
        .all()
    )
    weekly_sentiment = (
        db.session.query(
            func.date(SentimentAnalysis.created_at),
            func.avg(SentimentAnalysis.sentiment_score),
        )
        .filter(SentimentAnalysis.created_at >= since_7d)
        .group_by(func.date(SentimentAnalysis.created_at))
        .order_by(func.date(SentimentAnalysis.created_at))
        .all()
    )
    counselor_workload = (
        db.session.query(
            Counselor.full_name,
            func.count(Patient.id),
        )
        .outerjoin(Patient, Patient.assigned_counselor_id == Counselor.id)
        .group_by(Counselor.id, Counselor.full_name)
        .all()
    )
    total_workflow = Patient.query.filter(Patient.workflow_status.isnot(None)).count()
    resolved_count = Patient.query.filter(Patient.workflow_status == "RESOLVED").count()
    resolution_rate = round((resolved_count / total_workflow * 100), 1) if total_workflow else 0.0
    escalation_by_day = (
        db.session.query(func.date(Escalation.created_at), func.count(Escalation.id))
        .filter(Escalation.created_at >= since_7d)
        .group_by(func.date(Escalation.created_at))
        .order_by(func.date(Escalation.created_at))
        .all()
    )
    # Heatmap: risk events by day-of-week (0=Mon) and hour
    risk_rows = (
        RiskAnalysis.query.filter(RiskAnalysis.created_at >= since)
        .with_entities(RiskAnalysis.created_at, RiskAnalysis.risk_level)
        .all()
    )
    heatmap = {}
    for dt, level in risk_rows:
        if not dt:
            continue
        key = f"{dt.weekday()}_{dt.hour}"
        if key not in heatmap:
            heatmap[key] = {"dow": dt.weekday(), "hour": dt.hour, "count": 0, "critical": 0}
        heatmap[key]["count"] += 1
        if level in ("Critical", "High"):
            heatmap[key]["critical"] += 1

    return jsonify({
        "total_patients": total_patients,
        "risk_distribution": {k: v for k, v in risk_dist},
        "sentiment_distribution": {k: v for k, v in sentiment_dist},
        "escalations_30d": escalations,
        "phq_avg": float(phq_avg or 0),
        "gad_avg": float(gad_avg or 0),
        "daily_cases": [{"date": str(d), "count": c} for d, c in daily_cases],
        "daily_crisis_count": [{"date": str(d), "count": c} for d, c in daily_crisis],
        "weekly_sentiment_trend": [
            {"date": str(d), "avg_score": round(float(s or 0) * 100, 1)} for d, s in weekly_sentiment
        ],
        "escalation_count_7d": sum(c for _, c in escalation_by_day),
        "escalation_by_day": [{"date": str(d), "count": c} for d, c in escalation_by_day],
        "counselor_workload": [{"name": n or "Unassigned", "patients": c} for n, c in counselor_workload],
        "resolution_rate": resolution_rate,
        "resolved_count": resolved_count,
        "heatmap_cells": list(heatmap.values()),
    })


@admin_bp.get("/patients")
@jwt_required()
@role_required("ADMIN")
def list_patients():
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return jsonify({
        "patients": [
            {
                "id": p.id,
                "patient_id": p.patient_id,
                "full_name": p.full_name,
                "email": p.user.email if p.user else None,
                "latest_risk_level": p.latest_risk_level,
                "status": p.status.value if p.status else "ACTIVE",
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in patients
        ]
    })


@admin_bp.delete("/patients/<int:patient_id>")
@jwt_required()
@role_required("ADMIN")
def remove_patient(patient_id: int):
    patient = Patient.query.get_or_404(patient_id)
    name = patient.full_name
    code = patient.patient_id
    delete_patient_account(patient)
    audit_log(int(get_jwt_identity()), "DELETE_PATIENT", "patient", {"patient_id": code, "name": name})
    return jsonify({"message": f"Patient {code} deleted"})


@admin_bp.get("/counselors")
@jwt_required()
@role_required("ADMIN")
def list_counselors():
    counselors = Counselor.query.order_by(Counselor.created_at.desc()).all()
    return jsonify({
        "counselors": [
            {
                "id": c.id,
                "counselor_id": c.counselor_id,
                "full_name": c.full_name,
                "email": c.user.email if c.user else None,
                "specialization": c.specialization,
            }
            for c in counselors
        ]
    })


@admin_bp.post("/counselors")
@jwt_required()
@role_required("ADMIN")
def add_counselor():
    data = request.get_json() or {}
    required = ["full_name", "email", "password"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": "full_name, email, and password are required"}), 400
    try:
        counselor = create_counselor_account(
            full_name=data["full_name"],
            email=data["email"],
            password=data["password"],
            phone=data.get("phone"),
            specialization=data.get("specialization"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    audit_log(int(get_jwt_identity()), "CREATE_COUNSELOR", "counselor", {"counselor_id": counselor.counselor_id})
    return jsonify({
        "counselor": {
            "id": counselor.id,
            "counselor_id": counselor.counselor_id,
            "full_name": counselor.full_name,
        }
    }), 201
