import enum
from datetime import datetime

from app.extensions import db


class SessionRequestType(enum.Enum):
    CALLBACK = "CALLBACK"
    CHAT_SESSION = "CHAT_SESSION"


class SessionRequestStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    COMPLETED = "COMPLETED"


class SessionRequest(db.Model):
    __tablename__ = "session_requests"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey("counselors.id"), index=True)
    request_type = db.Column(db.Enum(SessionRequestType), nullable=False)
    status = db.Column(
        db.Enum(SessionRequestStatus),
        default=SessionRequestStatus.PENDING,
        nullable=False,
        index=True,
    )
    message = db.Column(db.Text)
    preferred_contact = db.Column(db.String(64))
    counselor_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship("Patient", backref=db.backref("session_requests", lazy="dynamic"))
    counselor = db.relationship("Counselor", backref=db.backref("session_requests", lazy="dynamic"))
