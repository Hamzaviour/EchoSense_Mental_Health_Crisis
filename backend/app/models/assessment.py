from datetime import datetime

from app.extensions import db


class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    assessment_type = db.Column(db.String(16), nullable=False)  # PHQ9, GAD7, WHO5
    question_number = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)  # list of {value, label}


class Phq9Result(db.Model):
    __tablename__ = "phq9_results"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    total_score = db.Column(db.Integer, nullable=False)
    severity = db.Column(db.String(64))
    responses = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Gad7Result(db.Model):
    __tablename__ = "gad7_results"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    total_score = db.Column(db.Integer, nullable=False)
    severity = db.Column(db.String(64))
    responses = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Who5Result(db.Model):
    __tablename__ = "who5_results"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    raw_score = db.Column(db.Integer, nullable=False)
    wellbeing_index = db.Column(db.Float)
    severity = db.Column(db.String(64))
    responses = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
