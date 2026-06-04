from datetime import datetime

from app.extensions import db


class SentimentAnalysis(db.Model):
    __tablename__ = "sentiment_analysis"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    message_id = db.Column(db.Integer, db.ForeignKey("chat_messages.id"))
    sentiment_score = db.Column(db.Float)
    sentiment_label = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class RiskAnalysis(db.Model):
    __tablename__ = "risk_analysis"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    message_id = db.Column(db.Integer, db.ForeignKey("chat_messages.id"))
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(32), nullable=False)
    component_breakdown = db.Column(db.JSON)
    suicide_flag = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
