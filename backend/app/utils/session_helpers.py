from app.extensions import db
from app.models import Session


def get_active_session(patient):
    session = Session.query.filter_by(patient_id=patient.id, is_active=True).first()
    if not session:
        session = Session(patient_id=patient.id, is_active=True)
        db.session.add(session)
        db.session.flush()
    return session
