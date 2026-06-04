from datetime import datetime

from app.extensions import db


class TherapyPlan(db.Model):
    __tablename__ = "therapy_plans"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    weekly_goals = db.Column(db.JSON, nullable=False, default=list)
    coping_tasks = db.Column(db.JSON, nullable=False, default=list)
    behavioral_suggestions = db.Column(db.JSON, nullable=False, default=list)
    summary = db.Column(db.Text)
    ai_generated = db.Column(db.Boolean, default=True)
    pdf_path = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient", backref=db.backref("therapy_plans", lazy="dynamic"))
