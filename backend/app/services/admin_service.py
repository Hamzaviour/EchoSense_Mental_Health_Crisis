"""Admin operations — patient removal, counselor creation."""

from app.extensions import db
from app.models import (
    AssessmentAnswer,
    AssessmentScore,
    AssessmentSession,
    ChatMessage,
    Counselor,
    Escalation,
    Gad7Result,
    Notification,
    Patient,
    Phq9Result,
    RiskAnalysis,
    SentimentAnalysis,
    Session,
    TherapyPlan,
    User,
    Who5Result,
)
from app.models.escalation import PdfReport
from app.utils.helpers import generate_counselor_id, hash_password


def delete_patient_account(patient: Patient) -> None:
    pid = patient.id
    uid = patient.user_id

    AssessmentAnswer.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    AssessmentScore.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    AssessmentSession.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    SentimentAnalysis.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    RiskAnalysis.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    Phq9Result.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    Gad7Result.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    Who5Result.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    TherapyPlan.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    PdfReport.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    Escalation.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    Notification.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    ChatMessage.query.filter_by(patient_id=pid).delete(synchronize_session=False)
    Session.query.filter_by(patient_id=pid).delete(synchronize_session=False)

    db.session.delete(patient)
    user = User.query.get(uid)
    if user:
        db.session.delete(user)
    db.session.commit()


def create_counselor_account(full_name: str, email: str, password: str, phone: str = None, specialization: str = None):
    from app.models.user import UserRole

    email = email.lower().strip()
    if User.query.filter_by(email=email).first():
        raise ValueError("Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(password),
        role=UserRole.COUNSELOR,
    )
    db.session.add(user)
    db.session.flush()
    counselor = Counselor(
        user_id=user.id,
        counselor_id=generate_counselor_id(),
        full_name=full_name.strip(),
        phone=phone,
        specialization=specialization or "General Counseling",
    )
    db.session.add(counselor)
    db.session.commit()
    return counselor
