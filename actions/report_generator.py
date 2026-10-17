"""
PDF Report Generator for TinyFish Agent Operations

Generates professional, structured PDF reports from agent automation results.
Includes executive summaries, key findings, source citations, and diagnostic
information for partial or failed operations.

Phase 5 Component: Transforms raw agent outputs into user-ready deliverables.
"""

import json
import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.colors import HexColor

from core.logger import get_logger

log = get_logger(__name__)


# ── Path Configuration ─────────────────────────────────────────────────────────

def _get_base_dir() -> Path:
    """Get the repository root directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _get_base_dir()
REPORTS_DIR = BASE_DIR / "reports"


# ── Report Schema & Data Structures ────────────────────────────────────────────

class ReportData:
    """Structured data container for PDF report generation."""

    def __init__(
        self,
        title: str,
        target_url: str,
        run_id: Optional[str] = None,
        status: str = "UNKNOWN",
        timestamp: Optional[str] = None,
        executive_summary: str = "",
        key_findings: List[Dict[str, str]] = None,
        sources: List[Dict[str, str]] = None,
        raw_result: Optional[str] = None,
        error_message: Optional[str] = None,
        goal: Optional[str] = None,
    ):
        self.title = title
        self.target_url = target_url
        self.run_id = run_id or "N/A"
        self.status = status
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.executive_summary = executive_summary
        self.key_findings = key_findings or []
        self.sources = sources or []
        self.raw_result = raw_result
        self.error_message = error_message
        self.goal = goal


# ── PDF Generation Engine ──────────────────────────────────────────────────────

def generate_pdf_report(
    report_data: ReportData,
    output_filename: Optional[str] = None
) -> Path:
    """
    Generate a professional PDF report from agent operation data.

    Args:
        report_data: ReportData instance with all report sections
        output_filename: Optional custom filename (without path)

    Returns:
        Path: Full path to the generated PDF file

    Raises:
        RuntimeError: If PDF generation fails
    """
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(exist_ok=True)

    # Generate timestamped filename if not provided
    if not output_filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create safe slug from title
        title_slug = "".join(c if c.isalnum() else "_" for c in report_data.title[:40])
        output_filename = f"report_{timestamp}_{title_slug}.pdf"

    output_path = REPORTS_DIR / output_filename

    log.info(f"[ReportGen] Generating PDF: {output_path}")

    try:
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )

        # Build content elements
        story = []
        styles = getSampleStyleSheet()

        # Add custom styles
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=6,
            alignment=TA_CENTER,
        ))

        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
        ))

        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#2c3e50'),
            spaceBefore=12,
            spaceAfter=8,
        ))

        styles.add(ParagraphStyle(
            name='WarningBox',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#856404'),
            backColor=HexColor('#fff3cd'),
            borderColor=HexColor('#ffeeba'),
            borderWidth=1,
            borderPadding=8,
            spaceAfter=12,
        ))

        # ── Header Section ─────────────────────────────────────────────────────

        story.append(Paragraph("OPERO INTELLIGENCE REPORT", styles['ReportTitle']))
        story.append(Spacer(1, 0.1*inch))

        subtitle = f"Document Title: {report_data.title}"
        story.append(Paragraph(subtitle, styles['ReportSubtitle']))

        # Metadata table
        metadata = [
            ["Target:", report_data.target_url],
            ["Status:", report_data.status],
            ["Run ID:", report_data.run_id],
            ["Generated:", _format_timestamp(report_data.timestamp)],
        ]

        metadata_table = Table(metadata, colWidths=[1.5*inch, 5*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        story.append(metadata_table)
        story.append(Spacer(1, 0.3*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#cccccc')))
        story.append(Spacer(1, 0.2*inch))

        # ── Status-Dependent Warning ───────────────────────────────────────────

        if report_data.status in ("FAILED", "TIMED_OUT", "CANCELLED"):
            warning = _build_status_warning(report_data)
            if warning:
                story.append(warning)
                story.append(Spacer(1, 0.15*inch))

        # ── Goal Section (if available) ────────────────────────────────────────

        if report_data.goal:
            story.append(Paragraph("Operation Goal", styles['SectionHeading']))
            story.append(Paragraph(report_data.goal, styles['BodyText']))
            story.append(Spacer(1, 0.15*inch))

        # ── Executive Summary ──────────────────────────────────────────────────

        if report_data.executive_summary:
            story.append(Paragraph("Executive Summary", styles['SectionHeading']))

            # Split into paragraphs for better readability
            paragraphs = report_data.executive_summary.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), styles['BodyText']))
                    story.append(Spacer(1, 0.1*inch))

            story.append(Spacer(1, 0.1*inch))

        # ── Key Findings ───────────────────────────────────────────────────────

        if report_data.key_findings:
            story.append(Paragraph("Key Findings & Extracted Data", styles['SectionHeading']))

            findings_table_data = [["Finding", "Value"]]
            findings_table_data.extend([
                [finding.get('label', 'N/A'), finding.get('value', 'N/A')]
                for finding in report_data.key_findings
            ])

            findings_table = Table(findings_table_data, colWidths=[2.5*inch, 4*inch])
            findings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f8f9fa')]),
            ]))

            story.append(findings_table)
            story.append(Spacer(1, 0.2*inch))

        # ── Raw Result (if no structured findings) ─────────────────────────────

        elif report_data.raw_result:
            story.append(Paragraph("Result Data", styles['SectionHeading']))

            # Truncate very long results
            result_text = report_data.raw_result
            if len(result_text) > 3000:
                result_text = result_text[:3000] + "\n\n... (result truncated for readability)"

            story.append(Paragraph(result_text, styles['BodyText']))
            story.append(Spacer(1, 0.2*inch))

        # ── Error Information ──────────────────────────────────────────────────

        if report_data.error_message:
            story.append(Paragraph("Error Details", styles['SectionHeading']))

            error_style = ParagraphStyle(
                name='ErrorText',
                parent=styles['BodyText'],
                textColor=HexColor('#721c24'),
                backColor=HexColor('#f8d7da'),
                borderColor=HexColor('#f5c6cb'),
                borderWidth=1,
                borderPadding=8,
            )

            story.append(Paragraph(report_data.error_message, error_style))
            story.append(Spacer(1, 0.2*inch))

        # ── Sources & Evidence ─────────────────────────────────────────────────

        if report_data.sources:
            story.append(Paragraph("Sources & Evidence", styles['SectionHeading']))

            for idx, source in enumerate(report_data.sources, 1):
                source_text = f"<b>[{idx}]</b> {source.get('title', 'Untitled')}"
                story.append(Paragraph(source_text, styles['BodyText']))

                url_text = f"<font color='#2980b9'>{source.get('url', 'N/A')}</font>"
                story.append(Paragraph(url_text, styles['Normal']))

                if source.get('accessed_at'):
                    access_text = f"<i>Accessed: {_format_timestamp(source['accessed_at'])}</i>"
                    story.append(Paragraph(access_text, styles['Normal']))

                story.append(Spacer(1, 0.1*inch))

        # ── Footer ─────────────────────────────────────────────────────────────

        story.append(Spacer(1, 0.3*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#cccccc')))
        story.append(Spacer(1, 0.1*inch))

        footer_text = (
            f"Generated autonomously by <b>Opero2 × TinyFish</b> · "
            f"Status: <b>{report_data.status}</b> · "
            f"Confidential / User-Initiated"
        )

        footer_style = ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#666666'),
            alignment=TA_CENTER,
        )

        story.append(Paragraph(footer_text, footer_style))

        # ── Build PDF ──────────────────────────────────────────────────────────

        doc.build(story)

        log.info(f"[ReportGen] PDF generated successfully: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"[ReportGen] Failed to generate PDF: {e}")
        raise RuntimeError(f"PDF generation failed: {e}")


# ── Helper Functions ───────────────────────────────────────────────────────────

def _format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to human-readable format."""
    try:
        dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return timestamp


def _build_status_warning(report_data: ReportData) -> Optional[Paragraph]:
    """Build a warning box for non-successful operations."""
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()

    warning_messages = {
        "TIMED_OUT": (
            "⚠️ <b>OPERATION TIMED OUT</b><br/>"
            "This report may contain partial data. The agent operation exceeded the "
            "local timeout threshold but may have continued executing remotely. "
            "Check the TinyFish dashboard for the complete operation status."
        ),
        "FAILED": (
            "⚠️ <b>OPERATION FAILED</b><br/>"
            "This report documents a failed agent operation. Review the error details "
            "section below for diagnostic information."
        ),
        "CANCELLED": (
            "⚠️ <b>OPERATION CANCELLED</b><br/>"
            "This operation was cancelled by the user or system before completion. "
            "The report may contain partial or no data."
        ),
    }

    message = warning_messages.get(report_data.status)
    if not message:
        return None

    warning_style = ParagraphStyle(
        name='Warning',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#856404'),
        backColor=HexColor('#fff3cd'),
        borderColor=HexColor('#ffeeba'),
        borderWidth=1,
        borderPadding=10,
        spaceAfter=12,
    )

    return Paragraph(message, warning_style)


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_report_from_history(
    run_id: Optional[str] = None,
    title: Optional[str] = None
) -> Path:
    """
    Generate a PDF report from TinyFish operation history.

    Args:
        run_id: Specific run ID to report on (uses latest if None)
        title: Custom report title (auto-generated if None)

    Returns:
        Path: Path to generated PDF file

    Raises:
        RuntimeError: If history file not found or report generation fails
    """
    history_file = BASE_DIR / "actions" / "tinyfish_history.json"

    if not history_file.exists():
        raise RuntimeError(
            "No operation history found. Run at least one agent operation first."
        )

    # Load history
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    if not history:
        raise RuntimeError("Operation history is empty.")

    # Find target entry
    if run_id:
        entry = next((e for e in history if e.get('run_id') == run_id), None)
        if not entry:
            raise RuntimeError(f"Run ID {run_id} not found in history.")
    else:
        # Use most recent entry
        entry = history[-1]

    # Build report data from history entry
    report_data = ReportData(
        title=title or f"Agent Operation Report: {entry.get('url', 'Unknown Target')}",
        target_url=entry.get('url', 'N/A'),
        run_id=entry.get('run_id'),
        status=entry.get('status', 'UNKNOWN'),
        timestamp=entry.get('timestamp'),
        goal=entry.get('goal'),
        error_message=entry.get('error'),
        executive_summary=_build_summary_from_history(entry),
    )

    # Add source if available
    if entry.get('url'):
        report_data.sources = [{
            'title': entry.get('url'),
            'url': entry.get('url'),
            'accessed_at': entry.get('timestamp'),
        }]

    return generate_pdf_report(report_data)


def _build_summary_from_history(entry: Dict[str, Any]) -> str:
    """Build executive summary from history entry."""
    if entry.get('success'):
        return (
            f"Agent operation completed successfully.\n\n"
            f"Goal: {entry.get('goal', 'N/A')}\n\n"
            f"The operation executed against {entry.get('url')} and completed "
            f"with status {entry.get('status')}. Detailed results were captured "
            f"in the operation history."
        )
    else:
        return (
            f"Agent operation failed or did not complete successfully.\n\n"
            f"Goal: {entry.get('goal', 'N/A')}\n\n"
            f"Status: {entry.get('status')}\n\n"
            f"Error: {entry.get('error', 'Unknown error')}"
        )
