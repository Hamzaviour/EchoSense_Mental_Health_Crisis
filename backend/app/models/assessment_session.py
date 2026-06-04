import enum
from datetime import datetime

from app.extensions import db


class SessionStatus(enum.Enum):
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DECLINED = "DECLINED"


class AssessmentSession(db.Model):
    __tablename__ = "assessment_sessions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    status = db.Column(db.Enum(SessionStatus), default=SessionStatus.OFFERED)
    assessment_types = db.Column(db.JSON, nullable=False)  # ["PHQ9", "GAD7"]
    current_type = db.Column(db.String(16))
    current_question_index = db.Column(db.Integer, default=0)
    progress_percent = db.Column(db.Float, default=0.0)
    offered_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    crisis_skipped = db.Column(db.Boolean, default=False)

    answers = db.relationship("AssessmentAnswer", back_populates="session", lazy="dynamic")
    scores = db.relationship("AssessmentScore", back_populates="session", lazy="dynamic")


class AssessmentAnswer(db.Model):
    __tablename__ = "assessment_answers"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("assessment_sessions.id"), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    assessment_type = db.Column(db.String(16), nullable=False)
    answer_value = db.Column(db.Integer, nullable=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship("AssessmentSession", back_populates="answers")


class AssessmentScore(db.Model):
    __tablename__ = "assessment_scores"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("assessment_sessions.id"), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    assessment_type = db.Column(db.String(16), nullable=False)
    partial_score = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Integer, default=0)
    progress_percent = db.Column(db.Float, default=0.0)
    severity = db.Column(db.String(64))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = db.relationship("AssessmentSession", back_populates="scores")
