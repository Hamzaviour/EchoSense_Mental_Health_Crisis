from datetime import datetime

from app.extensions import db


class Escalation(db.Model):
    __tablename__ = "escalations"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey("counselors.id"))
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(32), default="SENT")  # SENT, ACKNOWLEDGED, RESOLVED, OPEN
    ai_summary = db.Column(db.Text)
    counselor_notes = db.Column(db.Text)
    helpline_forwarded = db.Column(db.Boolean, default=False)
    helpline_reference = db.Column(db.String(64))
    acknowledged_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey("counselors.id"))
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"))
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(64))  # ALERT, ESCALATION, TRIAGE
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class PdfReport(db.Model):
    __tablename__ = "pdf_reports"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    escalation_id = db.Column(db.Integer, db.ForeignKey("escalations.id"))
    report_type = db.Column(db.String(64))  # EMERGENCY, CLINICAL_SUMMARY, ESCALATION
    file_path = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
