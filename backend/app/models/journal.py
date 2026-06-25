import enum
from datetime import datetime

from app.extensions import db


class JournalEntryType(enum.Enum):
    TEXT = "TEXT"
    VOICE = "VOICE"


class JournalEntry(db.Model):
    __tablename__ = "journal_entries"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    entry_type = db.Column(db.Enum(JournalEntryType), default=JournalEntryType.TEXT, nullable=False)
    content = db.Column(db.Text, nullable=False)
    transcript = db.Column(db.Text)
    ai_summary = db.Column(db.Text)
    emotions = db.Column(db.JSON, default=list)
    coping_strategies = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient", backref=db.backref("journal_entries", lazy="dynamic"))
