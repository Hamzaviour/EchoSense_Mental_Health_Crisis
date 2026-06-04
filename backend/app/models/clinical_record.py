from datetime import datetime

from app.extensions import db


class PatientClinicalRecord(db.Model):
    __tablename__ = "patient_clinical_records"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), unique=True, nullable=False, index=True)
    counselor_notes = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey("counselors.id"))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship("Patient", backref=db.backref("clinical_record", uselist=False))
