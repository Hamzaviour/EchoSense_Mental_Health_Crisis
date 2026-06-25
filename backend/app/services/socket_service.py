"""Socket.IO real-time notifications."""

import os

socketio = None


def init_socketio(app):
    global socketio
    from flask_socketio import SocketIO

    async_mode = os.getenv("SOCKETIO_ASYNC_MODE", "eventlet")
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)
    return socketio


def emit_counselor_notification(payload: dict):
    if socketio:
        socketio.emit("counselor_notification", payload, room="counselors")


def emit_counselor_alert(counselor_id: int, payload: dict):
    if socketio:
        socketio.emit("counselor_alert", payload, room=f"counselor_{counselor_id}")
        socketio.emit("counselor_notification", payload, room="counselors")


def emit_patient_takeover(patient_id: int, payload: dict):
    if socketio:
        socketio.emit("counselor_takeover", payload, room=f"patient_{patient_id}")
        socketio.emit("counselor_message", payload, room=f"patient_{patient_id}")


def emit_queue_update():
    if socketio:
        socketio.emit("queue_update", {"refresh": True})


def broadcast_patient_update(patient_id: int, payload: dict):
    """Notify all counselors of live patient / assessment / risk updates."""
    if socketio:
        socketio.emit("patient_live_update", payload, room="counselors")
        socketio.emit("patient_live_update", payload)


def emit_patient_message(patient_id: int, payload: dict):
    """Push a counselor message to the patient's live chat."""
    if socketio:
        socketio.emit("counselor_message", payload, room=f"patient_{patient_id}")


def broadcast_risk_alert(patient, risk):
    broadcast_patient_update(
        patient.id,
        {
            "event": "risk_alert",
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "patient_code": patient.patient_id,
            "risk_score": risk.risk_score,
            "risk_level": risk.risk_level,
            "priority": _priority_from_level(risk.risk_level),
            "sentiment_label": None,
        },
    )


def _priority_from_level(level: str) -> str:
    return {"Critical": "Critical", "High": "High", "Moderate": "Moderate"}.get(level, "Low")
