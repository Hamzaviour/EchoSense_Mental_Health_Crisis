from datetime import datetime

from app.extensions import db


class Counselor(db.Model):
    __tablename__ = "counselors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    counselor_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(32))
    specialization = db.Column(db.String(255))
    is_on_duty = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="counselor")
