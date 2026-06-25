import os
from datetime import datetime
from io import BytesIO

from reportlab.platypus import Paragraph, Spacer

from app.services.pdf_template import (
    build_and_save,
    bullet_section,
    create_document,
    disclaimer_block,
    get_echosense_styles,
    kv_table,
    para,
    report_header_meta,
    section_card,
)

from app.models import Gad7Result, Phq9Result, Who5Result

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")


def _ensure_dir():
    path = os.path.abspath(REPORTS_DIR)
    os.makedirs(path, exist_ok=True)
    return path


def _build_pdf(report_type: str, patient, filename_prefix: str, story: list) -> str:
    reports_path = _ensure_dir()
    filename = f"{filename_prefix}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(reports_path, filename)
    buffer = BytesIO()
    doc = create_document(buffer, report_type, patient_code=getattr(patient, "patient_id", None))
    build_and_save(doc, story, filepath)
    return filepath


def generate_emergency_pdf(patient, escalation, risk, assessments: dict, summary: str) -> str:
    styles = get_echosense_styles()
    story = report_header_meta(styles, patient.full_name, patient.patient_id)

    story.append(
        section_card(
            "Patient & Risk Overview",
            [
                kv_table([
                    ["Patient Name", patient.full_name],
                    ["Patient ID", patient.patient_id],
                    ["Phone", patient.phone or "N/A"],
                    ["Risk Score", f"{risk.risk_score:.1f}"],
                    ["Risk Level", risk.risk_level],
                    ["Escalation ID", str(escalation.id)],
                ]),
            ],
            styles,
        )
    )
    story.append(Spacer(1, 12))

    story.append(
        section_card(
            "Assessment Scores",
            [
                kv_table([
                    ["PHQ-9", str(assessments.get("phq9", "N/A"))],
                    ["GAD-7", str(assessments.get("gad7", "N/A"))],
                    ["WHO-5", str(assessments.get("who5", "N/A"))],
                ]),
            ],
            styles,
        )
    )
    story.append(Spacer(1, 12))

    story.append(
        section_card(
            "Conversation Summary",
            [para(summary, styles["EchoBody"])],
            styles,
        )
    )
    story.append(Spacer(1, 12))

    story.append(
        section_card(
            "Counselor Notes",
            [para(escalation.counselor_notes or "(Pending)", styles["EchoBody"])],
            styles,
        )
    )
    story.extend(
        disclaimer_block(
            styles,
            "URGENT — Crisis escalation document. For immediate mental health support, "
            "contact Umang: 0311-7786264 (24/7).",
        )
    )

    return _build_pdf(
        "crisis_escalation",
        patient,
        f"emergency_{patient.patient_id}_{escalation.id}",
        story,
    )


def generate_therapy_plan_pdf(patient, plan) -> str:
    styles = get_echosense_styles()
    story = report_header_meta(styles, patient.full_name, patient.patient_id)

    if plan.summary:
        story.append(section_card("Overview", [para(plan.summary, styles["EchoBody"])], styles))
        story.append(Spacer(1, 12))

    bullet_section(story, styles, "Weekly Goals", plan.weekly_goals or [])
    bullet_section(story, styles, "Coping Tasks", plan.coping_tasks or [])
    bullet_section(story, styles, "Behavioral Suggestions", plan.behavioral_suggestions or [])

    story.extend(
        disclaimer_block(
            styles,
            "This plan is AI-assisted wellness guidance, not a medical prescription. "
            "For crisis support, contact Umang: 0311-7786264 (24/7).",
        )
    )

    return _build_pdf("therapy_plan", patient, f"therapy_plan_{patient.patient_id}_{plan.id}", story)


def generate_clinical_case_report_pdf(patient, data: dict) -> str:
    """Full 9-section clinical case report for counselors and admins."""
    styles = get_echosense_styles()
    story = report_header_meta(styles, patient.full_name, patient.patient_id)

    identity = data.get("identity", {})
    story.append(
        section_card(
            "Section 1: Patient Identity",
            [
                kv_table([
                    ["Patient Name", identity.get("full_name", "N/A")],
                    ["Phone Number", identity.get("phone", "N/A")],
                    ["Age / Gender", f"{identity.get('age', 'N/A')} / {identity.get('gender', 'N/A')}"],
                    ["Patient ID", identity.get("patient_id", "N/A")],
                    ["Registration Date", identity.get("registration_date", "N/A")],
                ]),
            ],
            styles,
        )
    )
    story.append(Spacer(1, 12))

    story.append(
        section_card(
            "Section 2: Conversation Summary (AI Generated)",
            [para(data.get("conversation_summary") or "N/A", styles["EchoBody"])],
            styles,
        )
    )
    story.append(Spacer(1, 12))

    sentiment = data.get("sentiment", {})
    avg = sentiment.get("average")
    dist = sentiment.get("distribution") or {}
    dist_text = (
        ", ".join(f"{pct}% {label}" for label, pct in sorted(dist.items(), key=lambda x: -x[1]))
        if dist
        else "Insufficient data"
    )
    story.append(
        section_card(
            "Section 3: Sentiment Analysis Report",
            [
                para(f"<b>Average sentiment score:</b> {avg if avg is not None else 'N/A'}", styles["EchoBody"]),
                para(f"<b>Trend:</b> {sentiment.get('trend_note', 'N/A')}", styles["EchoBody"]),
                para(f"<b>Label distribution:</b> {dist_text}", styles["EchoBody"]),
            ],
            styles,
        )
    )
    story.append(Spacer(1, 12))

    risk = data.get("risk", {})
    triggers = risk.get("trigger_keywords") or []
    story.append(
        section_card(
            "Section 4: Risk Analysis (Triage Agent Output)",
            [
                kv_table([
                    ["Risk Score (0–100)", str(risk.get("score", "N/A"))],
                    ["Risk Level", risk.get("level", "N/A")],
                    ["Trigger keywords", ", ".join(triggers) if triggers else "None detected"],
                    ["Escalation status", risk.get("escalation_status", "None")],
                ]),
            ],
            styles,
        )
    )
    story.append(Spacer(1, 12))

    assessments = data.get("assessments", {})
    phq = assessments.get("phq9") or {}
    gad = assessments.get("gad7") or {}
    who5 = assessments.get("who5") or {}
    story.append(
        section_card(
            "Section 5: Assessment Results",
            [
                kv_table([
                    ["PHQ-9 Score", str(phq.get("score", "N/A"))],
                    ["PHQ-9 Severity", phq.get("severity") or "N/A"],
                    ["GAD-7 Score", str(gad.get("score", "N/A"))],
                    ["GAD-7 Severity", gad.get("severity") or "N/A"],
                    ["WHO-5 Wellbeing", str(who5.get("index", "N/A"))],
                    ["WHO-5 Severity", who5.get("severity") or "N/A"],
                ]),
            ],
            styles,
        )
    )
    story.append(Spacer(1, 12))

    story.append(
        section_card(
            "Section 6: AI Clinical Summary",
            [para(data.get("ai_clinical_summary") or "N/A", styles["EchoBody"])],
            styles,
        )
    )
    story.append(Spacer(1, 12))

    story.append(
        section_card(
            "Section 7: Counselor Notes (Manual)",
            [para(data.get("counselor_notes") or "(No notes recorded.)", styles["EchoBody"])],
            styles,
        )
    )
    story.append(Spacer(1, 12))

    recs = data.get("recommendations") or []
    rec_content = (
        [Paragraph(f"{i}. {rec}", styles["EchoBody"]) for i, rec in enumerate(recs, 1)]
        if recs
        else [para("No recommendations generated.", styles["EchoBodySmall"])]
    )
    story.append(section_card("Section 8: Recommendations", rec_content, styles))
    story.append(Spacer(1, 12))

    esc = data.get("escalation", {})
    sent = "Yes" if esc.get("sent_to_helpline") else "No"
    story.append(
        section_card(
            "Section 9: Escalation Status",
            [
                kv_table([
                    ["Sent to helpline?", sent],
                    ["Timestamp", esc.get("timestamp", "N/A")],
                    ["Action taken", esc.get("action_taken", "N/A")],
                    ["Helpline reference", esc.get("helpline_reference", "N/A")],
                ]),
            ],
            styles,
        )
    )
    story.extend(disclaimer_block(styles))

    return _build_pdf("patient_report", patient, f"clinical_case_{patient.patient_id}", story)


def generate_clinical_summary_pdf(patient, data: dict) -> str:
    styles = get_echosense_styles()
    story = report_header_meta(styles, patient.full_name, patient.patient_id)

    content = []
    for key, value in data.items():
        content.append(para(f"<b>{key}:</b> {value}", styles["EchoBody"]))
    story.append(section_card("Clinical Summary", content, styles))
    story.extend(disclaimer_block(styles))

    return _build_pdf("clinical_summary", patient, f"clinical_{patient.patient_id}", story)


def generate_assessment_report_pdf(patient, assessments: dict) -> str:
    """PDF report for PHQ-9, GAD-7, and WHO-5 assessment results."""
    styles = get_echosense_styles()
    story = report_header_meta(styles, patient.full_name, patient.patient_id)

    phq = assessments.get("phq9")
    gad = assessments.get("gad7")
    who5 = assessments.get("who5")

    rows = []
    if phq:
        rows.extend([
            ["PHQ-9 Score", str(phq.get("total_score", phq.get("score", "N/A")))],
            ["PHQ-9 Severity", phq.get("severity") or "N/A"],
            ["PHQ-9 Date", phq.get("date", "N/A")],
        ])
    if gad:
        rows.extend([
            ["GAD-7 Score", str(gad.get("total_score", gad.get("score", "N/A")))],
            ["GAD-7 Severity", gad.get("severity") or "N/A"],
            ["GAD-7 Date", gad.get("date", "N/A")],
        ])
    if who5:
        rows.extend([
            ["WHO-5 Wellbeing Index", str(who5.get("wellbeing_index", who5.get("index", "N/A")))],
            ["WHO-5 Severity", who5.get("severity") or "N/A"],
            ["WHO-5 Date", who5.get("date", "N/A")],
        ])

    if not rows:
        rows = [["Status", "No assessment results on file."]]

    story.append(section_card("Validated Assessment Scores", [kv_table(rows)], styles))
    story.append(Spacer(1, 12))

    interpretation = assessments.get("interpretation")
    if interpretation:
        story.append(
            section_card("Clinical Interpretation", [para(interpretation, styles["EchoBody"])], styles)
        )

    story.extend(disclaimer_block(styles))
    return _build_pdf("assessment", patient, f"assessment_{patient.patient_id}", story)


def generate_journal_export_pdf(patient, entries: list) -> str:
    """Export one or more journal entries with AI insights."""
    styles = get_echosense_styles()
    story = report_header_meta(styles, patient.full_name, patient.patient_id)

    if not entries:
        story.append(section_card("Journal Entries", [para("No entries to export.", styles["EchoBodySmall"])], styles))
    else:
        for i, entry in enumerate(entries):
            if i > 0:
                story.append(Spacer(1, 8))
            created = entry.get("created_at", "N/A")
            entry_type = entry.get("entry_type", "TEXT")
            title = f"Entry — {created[:10] if len(str(created)) >= 10 else created} ({entry_type})"
            content = [
                para(f"<b>AI Summary:</b> {entry.get('ai_summary') or '—'}", styles["EchoBody"]),
                Spacer(1, 6),
            ]
            emotions = entry.get("emotions") or []
            if emotions:
                content.append(para(f"<b>Emotions:</b> {', '.join(emotions)}", styles["EchoBody"]))
            strategies = entry.get("coping_strategies") or []
            if strategies:
                content.append(Spacer(1, 4))
                content.append(Paragraph("<b>Coping Strategies:</b>", styles["EchoBodySmall"]))
                content.extend(
                    Paragraph(f"{j}. {s}", styles["EchoBody"]) for j, s in enumerate(strategies, 1)
                )
            content.append(Spacer(1, 6))
            body = entry.get("content") or entry.get("transcript") or ""
            content.append(para(f"<b>Reflection:</b><br/>{body}", styles["EchoBody"]))
            story.append(section_card(title, content, styles))

    story.extend(
        disclaimer_block(
            styles,
            "Private journal export — handle in accordance with patient privacy policies. "
            "For crisis support, contact Umang: 0311-7786264 (24/7).",
        )
    )
    return _build_pdf("journal_export", patient, f"journal_{patient.patient_id}", story)


def build_assessment_report_data(patient) -> dict:
    """Gather latest PHQ-9, GAD-7, and WHO-5 results for PDF export."""
    phq = (
        Phq9Result.query.filter_by(patient_id=patient.id)
        .order_by(Phq9Result.created_at.desc())
        .first()
    )
    gad = (
        Gad7Result.query.filter_by(patient_id=patient.id)
        .order_by(Gad7Result.created_at.desc())
        .first()
    )
    who5 = (
        Who5Result.query.filter_by(patient_id=patient.id)
        .order_by(Who5Result.created_at.desc())
        .first()
    )
    data = {}
    if phq:
        data["phq9"] = {
            "total_score": phq.total_score,
            "severity": phq.severity,
            "date": phq.created_at.strftime("%Y-%m-%d %H:%M UTC") if phq.created_at else "N/A",
        }
    if gad:
        data["gad7"] = {
            "total_score": gad.total_score,
            "severity": gad.severity,
            "date": gad.created_at.strftime("%Y-%m-%d %H:%M UTC") if gad.created_at else "N/A",
        }
    if who5:
        data["who5"] = {
            "wellbeing_index": who5.wellbeing_index,
            "severity": who5.severity,
            "date": who5.created_at.strftime("%Y-%m-%d %H:%M UTC") if who5.created_at else "N/A",
        }
    parts = []
    if phq:
        parts.append(f"PHQ-9 indicates {phq.severity or 'unknown'} depression severity (score {phq.total_score}).")
    if gad:
        parts.append(f"GAD-7 indicates {gad.severity or 'unknown'} anxiety severity (score {gad.total_score}).")
    if who5:
        parts.append(
            f"WHO-5 wellbeing index is {who5.wellbeing_index} ({who5.severity or 'unknown'} wellbeing level)."
        )
    if parts:
        data["interpretation"] = " ".join(parts)
    return data
