from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.models import RiskAnalysis
from app.utils.decorators import role_required

risk_bp = Blueprint("risk", __name__, url_prefix="/api/risk")


@risk_bp.get("/patient/<int:patient_id>")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def patient_risk(patient_id: int):
    rows = (
        RiskAnalysis.query.filter_by(patient_id=patient_id)
        .order_by(RiskAnalysis.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify({
        "history": [
            {
                "id": r.id,
                "score": r.risk_score,
                "level": r.risk_level,
                "breakdown": r.component_breakdown,
                "suicide_flag": r.suicide_flag,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    })
