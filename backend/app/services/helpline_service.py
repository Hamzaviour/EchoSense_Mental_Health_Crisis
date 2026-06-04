"""Mock Umang helpline forwarding."""

import uuid
from datetime import datetime


def forward_to_umang_helpline(patient, escalation, pdf_path: str | None) -> dict:
    """Simulate sending escalation package to Umang helpline API."""
    reference = f"UMG-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    return {
        "success": True,
        "reference": reference,
        "helpline": "0311-7786264",
        "message": f"Escalation package for {patient.full_name} queued for Umang helpline review.",
        "pdf_attached": bool(pdf_path),
        "mock": True,
    }
