import os

from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)
load_dotenv()

from flask import Flask, jsonify
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import Config
from app.extensions import cors, db, jwt, limiter, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": [app.config["FRONTEND_URL"], "http://localhost:5173"]}},
        supports_credentials=True,
    )
    limiter.init_app(app)
    limiter.enabled = True

    from app.modules.admin import admin_bp
    from app.modules.assessment import assessment_bp
    from app.modules.auth import auth_bp
    from app.modules.chat import chat_bp
    from app.modules.counselor import counselor_bp
    from app.modules.escalation import escalation_bp
    from app.modules.patient import patient_bp
    from app.modules.risk import risk_bp

    for bp in (
        auth_bp,
        patient_bp,
        chat_bp,
        assessment_bp,
        counselor_bp,
        escalation_bp,
        admin_bp,
        risk_bp,
    ):
        app.register_blueprint(bp)

    try:
        from app.services.socket_service import init_socketio

        sio = init_socketio(app)
        app.extensions["socketio"] = sio

        @sio.on("connect")
        def on_connect():
            pass

        @sio.on("join_counselors")
        def on_join_counselors():
            from flask_socketio import join_room

            join_room("counselors")

        @sio.on("join_counselor")
        def on_join(data):
            from flask_socketio import join_room

            join_room("counselors")
            cid = data.get("counselor_id") if data else None
            if cid:
                join_room(f"counselor_{cid}")

        @sio.on("join_patient")
        def on_join_patient(data):
            from flask_socketio import join_room

            pid = data.get("patient_id") if data else None
            if pid:
                join_room(f"patient_{pid}")
    except ImportError:
        app.extensions["socketio"] = None

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "echo-sense"})

    @app.get("/metrics")
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    return app
