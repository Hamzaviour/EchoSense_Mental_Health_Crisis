import enum
from datetime import datetime

from app.extensions import db


class PatientStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    MODERATE = "MODERATE"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"


class WorkflowStatus(enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    FOLLOW_UP = "FOLLOW_UP"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    patient_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(32))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(32))
    status = db.Column(db.Enum(PatientStatus), default=PatientStatus.ACTIVE)
    consent_given = db.Column(db.Boolean, default=False)
    privacy_accepted = db.Column(db.Boolean, default=False)
    consent_at = db.Column(db.DateTime)
    latest_risk_score = db.Column(db.Float, default=0.0)
    latest_risk_level = db.Column(db.String(32), default="Low")
    workflow_status = db.Column(db.String(32), default=WorkflowStatus.NEW.value, index=True)
    assigned_counselor_id = db.Column(db.Integer, db.ForeignKey("counselors.id"))
    follow_up_at = db.Column(db.DateTime)
    session_scheduled_at = db.Column(db.DateTime)
    last_activity_at = db.Column(db.DateTime)
    ai_active = db.Column(db.Boolean, default=True)
    counselor_takeover_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="patient")
    sessions = db.relationship("Session", back_populates="patient", lazy="dynamic")
    messages = db.relationship("ChatMessage", back_populates="patient", lazy="dynamic")
    assigned_counselor = db.relationship("Counselor", foreign_keys=[assigned_counselor_id])
