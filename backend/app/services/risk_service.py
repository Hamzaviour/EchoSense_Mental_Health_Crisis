from flask import current_app

from app.extensions import db
from app.models import Gad7Result, Patient, Phq9Result, RiskAnalysis, SentimentAnalysis, Who5Result
from app.models.patient import PatientStatus
from app.services.classifier_service import classify_mental_health
from app.services.sentiment_service import analyze_sentiment
from app.utils.keywords import keyword_score
from app.utils.risk_scoring import (
    assessment_component,
    compute_ensemble_risk,
    trend_component,
)


def _latest_assessments(patient_id: int):
    phq = Phq9Result.query.filter_by(patient_id=patient_id).order_by(Phq9Result.created_at.desc()).first()
    gad = Gad7Result.query.filter_by(patient_id=patient_id).order_by(Gad7Result.created_at.desc()).first()
    who5 = Who5Result.query.filter_by(patient_id=patient_id).order_by(Who5Result.created_at.desc()).first()
    return (
        phq.total_score if phq else None,
        gad.total_score if gad else None,
        who5.raw_score if who5 else None,
    )


def _sentiment_trend(patient_id: int) -> list[float]:
    rows = (
        SentimentAnalysis.query.filter_by(patient_id=patient_id)
        .order_by(SentimentAnalysis.created_at.desc())
        .limit(5)
        .all()
    )
    return [r.sentiment_score or 0.5 for r in reversed(rows)]


def analyze_message_risk(patient_id: int, message_id: int, text: str) -> RiskAnalysis:
    sentiment = analyze_sentiment(text)
    kw = keyword_score(text)
    clf = classify_mental_health(
        text, enabled=current_app.config.get("RISK_CLASSIFIER_ENABLED", True)
    )
    phq, gad, who5 = _latest_assessments(patient_id)
    assess_comp = assessment_component(phq, gad, who5)
    trend = trend_component(_sentiment_trend(patient_id))

    score, level, breakdown = compute_ensemble_risk(
        sentiment["score"],
        sentiment["sentiment"],
        kw,
        clf["component_score"],
        assess_comp,
        trend,
        suicide_floor=kw.get("suicide_flag", False),
    )

    risk = RiskAnalysis(
        patient_id=patient_id,
        message_id=message_id,
        risk_score=score,
        risk_level=level,
        component_breakdown=breakdown,
        suicide_flag=kw.get("suicide_flag", False),
    )
    db.session.add(risk)

    patient = Patient.query.get(patient_id)
    if patient:
        patient.latest_risk_score = score
        patient.latest_risk_level = level
        if level == "Critical":
            patient.status = PatientStatus.CRITICAL
        elif level == "High":
            patient.status = PatientStatus.HIGH_RISK
        elif level == "Moderate":
            patient.status = PatientStatus.MODERATE

    return risk


def should_trigger_assessment(patient_id: int, risk_score: float, message_count: int) -> bool:
    return risk_score >= 31 or message_count < 3
