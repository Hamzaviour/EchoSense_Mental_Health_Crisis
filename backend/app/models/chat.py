import enum
from datetime import datetime

from app.extensions import db


class MessageRole(enum.Enum):
    PATIENT = "PATIENT"
    ASSISTANT = "ASSISTANT"
    COUNSELOR = "COUNSELOR"
    SYSTEM = "SYSTEM"


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    patient = db.relationship("Patient", back_populates="sessions")
    messages = db.relationship("ChatMessage", back_populates="session", lazy="dynamic")


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    role = db.Column(db.Enum(MessageRole), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_voice = db.Column(db.Boolean, default=False)
    rag_context_ids = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    session = db.relationship("Session", back_populates="messages")
    patient = db.relationship("Patient", back_populates="messages")
