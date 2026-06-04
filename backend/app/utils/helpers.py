import uuid

import bcrypt
from flask import request


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def generate_patient_id() -> str:
    return f"PAT-{uuid.uuid4().hex[:8].upper()}"


def generate_counselor_id() -> str:
    return f"CNS-{uuid.uuid4().hex[:8].upper()}"


def first_name(full_name: str) -> str:
    return full_name.strip().split()[0] if full_name else "there"


def audit_log(user_id, action: str, resource: str = None, details: dict = None):
    from app.extensions import db
    from app.models import AuditLog

    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        ip_address=request.remote_addr if request else None,
    )
    db.session.add(log)
