"""Global EchoSense PDF template — letterhead, footer, watermark, and shared styles."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# Brand palette
TEAL_PRIMARY = colors.HexColor("#0F766E")
TEAL_BANNER = colors.HexColor("#0D9488")
TEAL_ACCENT = colors.HexColor("#99F6E4")
TEAL_MUTED = colors.HexColor("#CCFBF1")
SLATE_DARK = colors.HexColor("#1E293B")
SLATE_MID = colors.HexColor("#475569")
SLATE_LIGHT = colors.HexColor("#64748B")
CARD_BG = colors.HexColor("#F8FAFC")
CARD_BORDER = colors.HexColor("#E2E8F0")

STRIP_WIDTH = 8
RIGHT_BORDER_WIDTH = 3
BANNER_HEIGHT = 0.92 * inch
FOOTER_HEIGHT = 0.72 * inch
MARGIN_LEFT = 0.78 * inch
MARGIN_RIGHT = 0.62 * inch
MARGIN_TOP = 1.28 * inch
MARGIN_BOTTOM = 0.82 * inch

PAGE_WIDTH, PAGE_HEIGHT = letter

REPORT_TYPES = {
    "patient_report": {
        "title": "Patient Clinical Case Report",
        "badge": "Patient Report",
        "badge_bg": "#0F766E",
        "badge_fg": "#FFFFFF",
        "code": "PCR",
    },
    "clinical_summary": {
        "title": "Clinical Summary",
        "badge": "Clinical Summary",
        "badge_bg": "#0369A1",
        "badge_fg": "#FFFFFF",
        "code": "CS",
    },
    "assessment": {
        "title": "Assessment Report",
        "badge": "Assessment Report",
        "badge_bg": "#7C3AED",
        "badge_fg": "#FFFFFF",
        "code": "AR",
    },
    "therapy_plan": {
        "title": "Weekly Therapy Plan",
        "badge": "Therapy Plan",
        "badge_bg": "#059669",
        "badge_fg": "#FFFFFF",
        "code": "TP",
    },
    "journal_export": {
        "title": "Journal Export",
        "badge": "Journal Export",
        "badge_bg": "#D97706",
        "badge_fg": "#FFFFFF",
        "code": "JE",
    },
    "crisis_escalation": {
        "title": "Crisis Escalation Report",
        "badge": "Crisis Escalation",
        "badge_bg": "#DC2626",
        "badge_fg": "#FFFFFF",
        "code": "CE",
    },
}

CONFIDENTIALITY_NOTICE = (
    "CONFIDENTIAL — This document contains protected health information. "
    "Unauthorized disclosure is prohibited under applicable privacy regulations."
)
SYSTEM_BRANDING = "EchoSense · AI-Powered Mental Health Platform"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def logo_path() -> str | None:
    for candidate in (
        _project_root() / "Echo_Logo.png",
        Path(__file__).resolve().parents[2] / "assets" / "Echo_Logo.png",
    ):
        if candidate.is_file():
            return str(candidate)
    return None


def generate_report_id(report_type: str, patient_code: str | None = None) -> str:
    cfg = REPORT_TYPES.get(report_type, REPORT_TYPES["patient_report"])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6].upper()
    patient_part = patient_code or "SYS"
    return f"ES-{cfg['code']}-{patient_part}-{stamp}-{suffix}"


def format_timestamp(dt: datetime | None = None) -> str:
    ts = dt or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.strftime("%B %d, %Y · %H:%M UTC")


def get_echosense_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="EchoBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=SLATE_DARK,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EchoBodySmall",
            parent=styles["EchoBody"],
            fontSize=9,
            leading=12,
            textColor=SLATE_MID,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EchoSectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=TEAL_PRIMARY,
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EchoCardTitle",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=TEAL_PRIMARY,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EchoMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=SLATE_LIGHT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EchoDisclaimer",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            leading=12,
            textColor=SLATE_MID,
            alignment=TA_JUSTIFY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EchoBullet",
            parent=styles["EchoBody"],
            leftIndent=14,
            bulletIndent=6,
            spaceAfter=4,
        )
    )
    return styles


class EchoSenseDocTemplate(BaseDocTemplate):
    """ReportLab document with standardized EchoSense letterhead and footer."""

    def __init__(
        self,
        filename,
        report_type: str,
        report_id: str,
        generated_at: datetime | None = None,
        **kwargs,
    ):
        self.report_type = report_type
        self.report_config = REPORT_TYPES.get(report_type, REPORT_TYPES["patient_report"])
        self.report_id = report_id
        self.generated_at = generated_at or datetime.now(timezone.utc)
        self._logo = logo_path()
        super().__init__(
            filename,
            pagesize=letter,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=MARGIN_TOP,
            bottomMargin=MARGIN_BOTTOM,
            **kwargs,
        )
        frame = Frame(
            MARGIN_LEFT,
            MARGIN_BOTTOM,
            PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT,
            PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM,
            id="content",
        )
        self.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self._draw_page_decor)])

    def _draw_page_decor(self, canvas, doc):
        canvas.saveState()

        # Left margin strip
        canvas.setFillColor(TEAL_PRIMARY)
        canvas.rect(0, 0, STRIP_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

        # Right accent border
        canvas.setFillColor(TEAL_ACCENT)
        canvas.rect(
            PAGE_WIDTH - RIGHT_BORDER_WIDTH,
            0,
            RIGHT_BORDER_WIDTH,
            PAGE_HEIGHT,
            fill=1,
            stroke=0,
        )

        # Watermark
        self._draw_watermark(canvas)

        # Top banner
        canvas.setFillColor(TEAL_BANNER)
        canvas.rect(STRIP_WIDTH, PAGE_HEIGHT - BANNER_HEIGHT, PAGE_WIDTH - STRIP_WIDTH, BANNER_HEIGHT, fill=1, stroke=0)
        canvas.setFillColor(TEAL_ACCENT)
        canvas.rect(STRIP_WIDTH, PAGE_HEIGHT - BANNER_HEIGHT, PAGE_WIDTH - STRIP_WIDTH, 2, fill=1, stroke=0)

        # Logo in banner
        logo_x = STRIP_WIDTH + 14
        logo_y = PAGE_HEIGHT - BANNER_HEIGHT + 10
        if self._logo:
            try:
                canvas.drawImage(
                    self._logo,
                    logo_x,
                    logo_y,
                    width=0.55 * inch,
                    height=0.55 * inch,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                pass

        text_x = logo_x + (0.62 * inch if self._logo else 0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(text_x, PAGE_HEIGHT - BANNER_HEIGHT + 38, "EchoSense")
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(TEAL_MUTED)
        canvas.drawString(text_x, PAGE_HEIGHT - BANNER_HEIGHT + 22, "Healthcare Intelligence Platform")

        # Report badge (color-coded)
        badge = self.report_config["badge"]
        badge_bg = colors.HexColor(self.report_config["badge_bg"])
        badge_w = len(badge) * 5.2 + 18
        badge_x = PAGE_WIDTH - RIGHT_BORDER_WIDTH - badge_w - 16
        badge_y = PAGE_HEIGHT - BANNER_HEIGHT + 28
        canvas.setFillColor(badge_bg)
        canvas.roundRect(badge_x, badge_y, badge_w, 16, 4, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor(self.report_config["badge_fg"]))
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.drawCentredString(badge_x + badge_w / 2, badge_y + 4.5, badge.upper())

        # Report title & meta (right side of banner)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 11)
        title = self.report_config["title"]
        canvas.drawRightString(PAGE_WIDTH - RIGHT_BORDER_WIDTH - 16, PAGE_HEIGHT - BANNER_HEIGHT + 52, title)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(TEAL_MUTED)
        canvas.drawRightString(
            PAGE_WIDTH - RIGHT_BORDER_WIDTH - 16,
            PAGE_HEIGHT - BANNER_HEIGHT + 38,
            f"Report ID: {self.report_id}",
        )
        canvas.drawRightString(
            PAGE_WIDTH - RIGHT_BORDER_WIDTH - 16,
            PAGE_HEIGHT - BANNER_HEIGHT + 26,
            f"Generated: {format_timestamp(self.generated_at)}",
        )

        # Footer
        footer_y = 28
        canvas.setStrokeColor(TEAL_ACCENT)
        canvas.setLineWidth(0.5)
        canvas.line(STRIP_WIDTH + 12, footer_y + 22, PAGE_WIDTH - RIGHT_BORDER_WIDTH - 12, footer_y + 22)

        canvas.setFillColor(SLATE_MID)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(STRIP_WIDTH + 14, footer_y + 10, CONFIDENTIALITY_NOTICE[:95])
        canvas.drawString(STRIP_WIDTH + 14, footer_y, CONFIDENTIALITY_NOTICE[95:])

        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(TEAL_PRIMARY)
        canvas.drawCentredString(PAGE_WIDTH / 2, footer_y + 6, SYSTEM_BRANDING)

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(SLATE_LIGHT)
        canvas.drawRightString(
            PAGE_WIDTH - RIGHT_BORDER_WIDTH - 14,
            footer_y + 6,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    def _draw_watermark(self, canvas):
        cx = PAGE_WIDTH / 2
        cy = PAGE_HEIGHT / 2
        canvas.saveState()
        canvas.setFillAlpha(0.06)
        if self._logo:
            try:
                reader = ImageReader(self._logo)
                w, h = reader.getSize()
                aspect = w / h
                draw_h = 2.8 * inch
                draw_w = draw_h * aspect
                canvas.drawImage(
                    self._logo,
                    cx - draw_w / 2,
                    cy - draw_h / 2,
                    width=draw_w,
                    height=draw_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                canvas.setFillColor(TEAL_PRIMARY)
                canvas.setFont("Helvetica-Bold", 48)
                canvas.drawCentredString(cx, cy, "EchoSense")
        else:
            canvas.setFillColor(TEAL_PRIMARY)
            canvas.setFont("Helvetica-Bold", 48)
            canvas.drawCentredString(cx, cy, "EchoSense")
        canvas.restoreState()


def create_document(
    buffer: BytesIO,
    report_type: str,
    report_id: str | None = None,
    patient_code: str | None = None,
    generated_at: datetime | None = None,
) -> EchoSenseDocTemplate:
    rid = report_id or generate_report_id(report_type, patient_code)
    return EchoSenseDocTemplate(
        buffer,
        report_type=report_type,
        report_id=rid,
        generated_at=generated_at,
    )


def build_and_save(doc: EchoSenseDocTemplate, story: list, filepath: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    doc.build(story)
    data = doc.filename.getvalue() if hasattr(doc.filename, "getvalue") else None
    if data is not None:
        with open(filepath, "wb") as f:
            f.write(data)
    return filepath


def report_header_meta(styles, patient_name: str | None = None, patient_id: str | None = None) -> list:
    """Optional patient context block below letterhead."""
    flowables = []
    if patient_name or patient_id:
        parts = []
        if patient_name:
            parts.append(f"<b>Patient:</b> {patient_name}")
        if patient_id:
            parts.append(f"<b>ID:</b> {patient_id}")
        flowables.append(Paragraph(" &nbsp;|&nbsp; ".join(parts), styles["EchoMeta"]))
        flowables.append(Spacer(1, 10))
    return flowables


def section_card(title: str, content: list, styles, width: float | None = None) -> Table:
    """Wrap section content in a styled card with teal accent bar."""
    card_width = width or (PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT)
    rows = [[Paragraph(f"<b>{title}</b>", styles["EchoCardTitle"])]]
    rows.extend([[item] for item in content])
    t = Table(rows, colWidths=[card_width])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("LINEBELOW", (0, 0), (-1, 0), 2, TEAL_PRIMARY),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (0, 0), 10),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
                ("TOPPADDING", (0, 1), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def kv_table(rows: list[list[str]], col_widths=None) -> Table:
    t = Table(rows, colWidths=col_widths or [155, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT - 155])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), TEAL_MUTED),
                ("TEXTCOLOR", (0, 0), (0, -1), TEAL_PRIMARY),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("GRID", (0, 0), (-1, -1), 0.4, CARD_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def para(text: str, style) -> Paragraph:
    return Paragraph((text or "N/A").replace("\n", "<br/>"), style)


def bullet_section(story: list, styles, title: str, items: list[str]):
    story.append(section_card(title, [Spacer(1, 4)] + [
        Paragraph(f"{i}. {item}", styles["EchoBody"]) for i, item in enumerate(items, 1)
    ] if items else [Paragraph("None recorded.", styles["EchoBodySmall"])], styles))
    story.append(Spacer(1, 12))


def disclaimer_block(styles, text: str | None = None) -> list:
    default = (
        "This document is generated by EchoSense for clinical and wellness support purposes. "
        "It does not replace professional medical diagnosis. "
        "For crisis support, contact Umang: 0311-7786264 (24/7)."
    )
    return [
        Spacer(1, 16),
        Paragraph(text or default, styles["EchoDisclaimer"]),
    ]
