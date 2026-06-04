import os

from flask import Blueprint, jsonify, send_file
from flask_jwt_extended import jwt_required

from app.models import Escalation, PdfReport
from app.utils.decorators import role_required

escalation_bp = Blueprint("escalation", __name__, url_prefix="/api/escalations")


@escalation_bp.get("")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def list_escalations():
    rows = Escalation.query.order_by(Escalation.created_at.desc()).limit(100).all()
    return jsonify({
        "escalations": [
            {
                "id": e.id,
                "patient_id": e.patient_id,
                "risk_score": e.risk_score,
                "risk_level": e.risk_level,
                "status": e.status,
                "created_at": e.created_at.isoformat(),
            }
            for e in rows
        ]
    })


@escalation_bp.get("/<int:escalation_id>/pdf")
@jwt_required()
@role_required("COUNSELOR", "ADMIN")
def download_pdf(escalation_id: int):
    pdf = PdfReport.query.filter_by(escalation_id=escalation_id).first()
    if not pdf or not pdf.file_path or not os.path.exists(pdf.file_path):
        return jsonify({"error": "PDF not found"}), 404
    return send_file(pdf.file_path, as_attachment=True, download_name=os.path.basename(pdf.file_path))
