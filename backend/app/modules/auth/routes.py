from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required

from app.extensions import db, limiter
from app.models import Counselor, Patient, User
from app.models.user import UserRole
from app.utils.helpers import audit_log, check_password, generate_counselor_id, generate_patient_id, hash_password

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
@limiter.limit("10 per hour")
def register():
    data = request.get_json() or {}
    required = ["full_name", "email", "password", "phone", "age", "gender"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        email=data["email"].lower(),
        password_hash=hash_password(data["password"]),
        role=UserRole.PATIENT,
    )
    db.session.add(user)
    db.session.flush()

    patient = Patient(
        user_id=user.id,
        patient_id=generate_patient_id(),
        full_name=data["full_name"],
        phone=data["phone"],
        age=int(data["age"]),
        gender=data["gender"],
    )
    db.session.add(patient)
    audit_log(user.id, "REGISTER", "patient", {"patient_id": patient.patient_id})
    db.session.commit()

    access = create_access_token(identity=str(user.id), additional_claims={"role": user.role.value})
    refresh = create_refresh_token(identity=str(user.id))
    return jsonify({
        "access_token": access,
        "refresh_token": refresh,
        "user": {"id": user.id, "email": user.email, "role": user.role.value},
        "patient": {"patient_id": patient.patient_id, "full_name": patient.full_name},
    }), 201


@auth_bp.post("/login")
@limiter.limit("20 per hour")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not check_password(password, user.password_hash):
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.is_active:
        return jsonify({"error": "Account disabled"}), 403

    audit_log(user.id, "LOGIN", "user")
    db.session.commit()

    access = create_access_token(identity=str(user.id), additional_claims={"role": user.role.value})
    refresh = create_refresh_token(identity=str(user.id))
    payload = {
        "access_token": access,
        "refresh_token": refresh,
        "user": {"id": user.id, "email": user.email, "role": user.role.value},
    }
    if user.role == UserRole.PATIENT and user.patient:
        payload["patient"] = {
            "patient_id": user.patient.patient_id,
            "full_name": user.patient.full_name,
            "consent_given": user.patient.consent_given,
        }
    if user.role == UserRole.COUNSELOR and user.counselor:
        payload["counselor"] = {"counselor_id": user.counselor.counselor_id, "full_name": user.counselor.full_name}
    return jsonify(payload)


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    access = create_access_token(identity=str(user.id), additional_claims={"role": user.role.value})
    return jsonify({"access_token": access})


@auth_bp.post("/register-counselor")
@limiter.limit("5 per hour")
def register_counselor():
    """Bootstrap endpoint for demo — create counselor accounts."""
    data = request.get_json() or {}
    if not all(data.get(f) for f in ["full_name", "email", "password"]):
        return jsonify({"error": "Missing fields"}), 400
    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "Email exists"}), 409

    user = User(
        email=data["email"].lower(),
        password_hash=hash_password(data["password"]),
        role=UserRole.COUNSELOR,
    )
    db.session.add(user)
    db.session.flush()
    counselor = Counselor(
        user_id=user.id,
        counselor_id=generate_counselor_id(),
        full_name=data["full_name"],
        phone=data.get("phone"),
        specialization=data.get("specialization", "General Counseling"),
    )
    db.session.add(counselor)
    db.session.commit()
    access = create_access_token(identity=str(user.id), additional_claims={"role": user.role.value})
    refresh = create_refresh_token(identity=str(user.id))
    return jsonify({"access_token": access, "refresh_token": refresh}), 201
