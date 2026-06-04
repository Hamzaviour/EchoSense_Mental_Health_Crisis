import os
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")


def _ensure_dir():
    path = os.path.abspath(REPORTS_DIR)
    os.makedirs(path, exist_ok=True)
    return path


def generate_emergency_pdf(patient, escalation, risk, assessments: dict, summary: str) -> str:
    reports_path = _ensure_dir()
    filename = f"emergency_{patient.patient_id}_{escalation.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(reports_path, filename)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Echo Sense — Emergency Escalation Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.utcnow().isoformat()} UTC", styles["Normal"]))
    story.append(Spacer(1, 12))

    data = [
        ["Patient Name", patient.full_name],
        ["Patient ID", patient.patient_id],
        ["Phone", patient.phone or "N/A"],
        ["Risk Score", f"{risk.risk_score:.1f}"],
        ["Risk Level", risk.risk_level],
        ["PHQ-9", str(assessments.get("phq9", "N/A"))],
        ["GAD-7", str(assessments.get("gad7", "N/A"))],
        ["WHO-5", str(assessments.get("who5", "N/A"))],
    ]
    t = Table(data, colWidths=[150, 350])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Conversation Summary</b>", styles["Heading2"]))
    story.append(Paragraph(summary.replace("\n", "<br/>"), styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Counselor Notes</b>", styles["Heading2"]))
    story.append(Paragraph(escalation.counselor_notes or "(Pending)", styles["Normal"]))
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        "<b>Helpline — Umang:</b> 0311-7786264 (24/7 mental health support)",
        styles["Normal"],
    ))

    doc.build(story)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return filepath


def generate_therapy_plan_pdf(patient, plan) -> str:
    reports_path = _ensure_dir()
    filename = f"therapy_plan_{patient.patient_id}_{plan.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(reports_path, filename)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Echo Sense — Weekly Therapy Plan</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"<b>Patient:</b> {patient.full_name} ({patient.patient_id})",
        styles["Normal"],
    ))
    story.append(Paragraph(
        f"<b>Generated:</b> {datetime.utcnow().strftime('%B %d, %Y')} UTC",
        styles["Normal"],
    ))
    story.append(Spacer(1, 16))

    if plan.summary:
        story.append(Paragraph("<b>Overview</b>", styles["Heading2"]))
        story.append(Paragraph(plan.summary, styles["Normal"]))
        story.append(Spacer(1, 12))

    def _bullet_section(title: str, items: list):
        story.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))
        for i, item in enumerate(items, 1):
            story.append(Paragraph(f"{i}. {item}", styles["Normal"]))
        story.append(Spacer(1, 12))

    _bullet_section("Weekly Goals", plan.weekly_goals or [])
    _bullet_section("Coping Tasks", plan.coping_tasks or [])
    _bullet_section("Behavioral Suggestions", plan.behavioral_suggestions or [])

    story.append(Spacer(1, 24))
    story.append(Paragraph(
        "<i>This plan is AI-assisted wellness guidance, not a medical prescription. "
        "For crisis support, contact Umang: 0311-7786264 (24/7).</i>",
        styles["Normal"],
    ))

    doc.build(story)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return filepath


def _section_heading(story, styles, title: str):
    story.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))


def _kv_table(rows: list[list[str]], col_widths=None):
    t = Table(rows, colWidths=col_widths or [160, 340])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def generate_clinical_case_report_pdf(patient, data: dict) -> str:
    """Full 9-section clinical case report for counselors and admins."""
    reports_path = _ensure_dir()
    filename = f"clinical_case_{patient.patient_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(reports_path, filename)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Echo Sense — Clinical Case Report</b>", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<b>Generated:</b> {data.get('generated_at', datetime.utcnow().isoformat())} UTC",
        styles["Normal"],
    ))
    story.append(Spacer(1, 16))

    identity = data.get("identity", {})
    _section_heading(story, styles, "Section 1: Patient Identity")
    story.append(_kv_table([
        ["Patient Name", identity.get("full_name", "N/A")],
        ["Phone Number", identity.get("phone", "N/A")],
        ["Age / Gender", f"{identity.get('age', 'N/A')} / {identity.get('gender', 'N/A')}"],
        ["Patient ID", identity.get("patient_id", "N/A")],
        ["Registration Date", identity.get("registration_date", "N/A")],
    ]))
    story.append(Spacer(1, 14))

    _section_heading(story, styles, "Section 2: Conversation Summary (AI Generated)")
    story.append(Paragraph(
        (data.get("conversation_summary") or "N/A").replace("\n", "<br/>"),
        styles["Normal"],
    ))
    story.append(Spacer(1, 14))

    sentiment = data.get("sentiment", {})
    _section_heading(story, styles, "Section 3: Sentiment Analysis Report")
    avg = sentiment.get("average")
    story.append(Paragraph(
        f"<b>Average sentiment score:</b> {avg if avg is not None else 'N/A'}",
        styles["Normal"],
    ))
    story.append(Paragraph(
        f"<b>Trend:</b> {sentiment.get('trend_note', 'N/A')}",
        styles["Normal"],
    ))
    dist = sentiment.get("distribution") or {}
    if dist:
        dist_lines = ", ".join(f"{pct}% {label}" for label, pct in sorted(dist.items(), key=lambda x: -x[1]))
        story.append(Paragraph(f"<b>Label distribution:</b> {dist_lines}", styles["Normal"]))
    else:
        story.append(Paragraph("<b>Label distribution:</b> Insufficient data", styles["Normal"]))
    story.append(Spacer(1, 14))

    risk = data.get("risk", {})
    _section_heading(story, styles, "Section 4: Risk Analysis (Triage Agent Output)")
    triggers = risk.get("trigger_keywords") or []
    story.append(_kv_table([
        ["Risk Score (0–100)", str(risk.get("score", "N/A"))],
        ["Risk Level", risk.get("level", "N/A")],
        ["Trigger keywords", ", ".join(triggers) if triggers else "None detected"],
        ["Escalation status", risk.get("escalation_status", "None")],
    ]))
    story.append(Spacer(1, 14))

    assessments = data.get("assessments", {})
    _section_heading(story, styles, "Section 5: Assessment Results")
    phq = assessments.get("phq9") or {}
    gad = assessments.get("gad7") or {}
    who5 = assessments.get("who5") or {}
    story.append(_kv_table([
        ["PHQ-9 Score", str(phq.get("score", "N/A"))],
        ["PHQ-9 Severity", phq.get("severity") or "N/A"],
        ["GAD-7 Score", str(gad.get("score", "N/A"))],
        ["GAD-7 Severity", gad.get("severity") or "N/A"],
        ["WHO-5 Wellbeing", str(who5.get("index", "N/A"))],
        ["WHO-5 Severity", who5.get("severity") or "N/A"],
    ]))
    story.append(Spacer(1, 14))

    _section_heading(story, styles, "Section 6: AI Clinical Summary")
    story.append(Paragraph(
        (data.get("ai_clinical_summary") or "N/A").replace("\n", "<br/>"),
        styles["Normal"],
    ))
    story.append(Spacer(1, 14))

    _section_heading(story, styles, "Section 7: Counselor Notes (Manual)")
    story.append(Paragraph(
        (data.get("counselor_notes") or "(No notes recorded.)").replace("\n", "<br/>"),
        styles["Normal"],
    ))
    story.append(Spacer(1, 14))

    recs = data.get("recommendations") or []
    _section_heading(story, styles, "Section 8: Recommendations")
    for i, rec in enumerate(recs, 1):
        story.append(Paragraph(f"{i}. {rec}", styles["Normal"]))
    if not recs:
        story.append(Paragraph("No recommendations generated.", styles["Normal"]))
    story.append(Spacer(1, 14))

    esc = data.get("escalation", {})
    _section_heading(story, styles, "Section 9: Escalation Status")
    sent = "Yes" if esc.get("sent_to_helpline") else "No"
    story.append(_kv_table([
        ["Sent to helpline?", sent],
        ["Timestamp", esc.get("timestamp", "N/A")],
        ["Action taken", esc.get("action_taken", "N/A")],
        ["Helpline reference", esc.get("helpline_reference", "N/A")],
    ]))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>Confidential clinical document — Echo Sense. For crisis support: Umang 0311-7786264 (24/7).</i>",
        styles["Normal"],
    ))

    doc.build(story)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return filepath


def generate_clinical_summary_pdf(patient, data: dict) -> str:
    reports_path = _ensure_dir()
    filename = f"clinical_{patient.patient_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(reports_path, filename)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>Echo Sense — Clinical Summary</b>", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Patient: {patient.full_name} ({patient.patient_id})", styles["Normal"]),
    ]
    for key, value in data.items():
        story.append(Paragraph(f"<b>{key}:</b> {value}", styles["Normal"]))
    doc.build(story)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return filepath
