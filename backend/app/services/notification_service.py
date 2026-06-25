"""Counselor live notifications."""

from app.extensions import db
from app.models import Counselor, Notification, Patient


def _broadcast(payload: dict):
    try:
        from app.services.socket_service import emit_counselor_notification

        emit_counselor_notification(payload)
    except Exception:
        pass


def create_counselor_notification(
    title: str,
    message: str,
    notification_type: str,
    patient_id: int | None = None,
    counselor_id: int | None = None,
    broadcast: bool = True,
) -> Notification:
    notif = Notification(
        counselor_id=counselor_id,
        patient_id=patient_id,
        title=title,
        message=message,
        notification_type=notification_type,
    )
    db.session.add(notif)
    db.session.flush()
    if broadcast:
        _broadcast({
            "id": notif.id,
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "patient_id": patient_id,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
        })
    return notif


def notify_all_counselors(
    title: str,
    message: str,
    notification_type: str,
    patient_id: int | None = None,
) -> None:
    counselors = Counselor.query.filter_by(is_on_duty=True).all()
    if not counselors:
        counselors = Counselor.query.limit(5).all()
    first = True
    for c in counselors:
        create_counselor_notification(
            title=title,
            message=message,
            notification_type=notification_type,
            patient_id=patient_id,
            counselor_id=c.id,
            broadcast=first,
        )
        first = False


def notify_critical_case(patient: Patient, risk_score: float) -> None:
    notify_all_counselors(
        title="New Critical Case",
        message=f"{patient.full_name} ({patient.patient_id}) — risk score {risk_score:.0f}. Immediate review required.",
        notification_type="CRITICAL_CASE",
        patient_id=patient.id,
    )


def notify_phq_completed(patient_id: int, score: int, severity: str) -> None:
    patient = Patient.query.get(patient_id)
    if not patient:
        return
    notify_all_counselors(
        title="PHQ Assessment Completed",
        message=f"{patient.full_name} completed PHQ-9 — score {score} ({severity}).",
        notification_type="PHQ_COMPLETED",
        patient_id=patient.id,
    )


def notify_counselor_mentioned(patient: Patient, detail: str = "") -> None:
    msg = f"{patient.full_name} ({patient.patient_id})"
    if detail:
        msg += f" — {detail}"
    notify_all_counselors(
        title="Counselor Mentioned",
        message=msg,
        notification_type="COUNSELOR_MENTIONED",
        patient_id=patient.id,
    )


def notify_session_request(patient: Patient, request_type: str, counselor_id: int | None = None) -> None:
    type_label = "callback" if request_type == "CALLBACK" else "chat session"
    msg = f"{patient.full_name} ({patient.patient_id}) requested a {type_label}."
    if counselor_id:
        create_counselor_notification(
            title="Session Request",
            message=msg,
            notification_type="SESSION_REQUEST",
            patient_id=patient.id,
            counselor_id=counselor_id,
            broadcast=True,
        )
    else:
        notify_all_counselors(
            title="Session Request",
            message=msg,
            notification_type="SESSION_REQUEST",
            patient_id=patient.id,
        )
