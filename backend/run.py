import os

from app import create_app

flask_app = create_app()
socketio = flask_app.extensions.get("socketio")

with flask_app.app_context():
    import app.models  # noqa: F401
    from app.extensions import db
    from sqlalchemy import inspect, text

    db.create_all()

    insp = inspect(db.engine)
    if "patient_clinical_records" not in insp.get_table_names():
        from app.models.clinical_record import PatientClinicalRecord  # noqa: F401
        db.create_all()

    def _ensure_columns(table: str, columns: dict[str, str]):
        try:
            insp = inspect(db.engine)
            if table not in insp.get_table_names():
                return
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, coldef in columns.items():
                if name not in existing:
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {coldef}"))
            db.session.commit()
        except Exception:
            db.session.rollback()

    _ensure_columns("patients", {
        "workflow_status": "VARCHAR(32) DEFAULT 'NEW'",
        "assigned_counselor_id": "INTEGER",
        "follow_up_at": "TIMESTAMP",
        "session_scheduled_at": "TIMESTAMP",
        "last_activity_at": "TIMESTAMP",
        "ai_active": "BOOLEAN DEFAULT TRUE",
        "counselor_takeover_at": "TIMESTAMP",
    })
    _ensure_columns("escalations", {
        "counselor_id": "INTEGER",
        "ai_summary": "TEXT",
        "helpline_reference": "VARCHAR(64)",
        "acknowledged_at": "TIMESTAMP",
        "resolved_at": "TIMESTAMP",
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_ENV") == "development"
    if socketio:
        socketio.run(flask_app, host="0.0.0.0", port=port, debug=debug, allow_unsafe_werkzeug=True)
    else:
        flask_app.run(host="0.0.0.0", port=port, debug=debug)
