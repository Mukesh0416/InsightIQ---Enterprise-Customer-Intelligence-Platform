"""
Report Generation Engine.

Generates PDF, Excel, CSV, and JSON reports for all report types.
Each report includes cover page, executive summary, KPIs, tables,
insights, recommendations, and metadata.
"""

from __future__ import annotations

import io
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import pandas as pd

from app.exceptions import ValidationError

logger = logging.getLogger(__name__)

_REPORT_DIR = Path("reports/generated")


def _ensure_dir() -> None:
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)


def _report_path(report_id: str, fmt: str) -> Path:
    return _REPORT_DIR / f"{report_id}.{fmt}"


# ── PDF Generator ─────────────────────────────────────────────────────────

def _generate_pdf(report_id: str, report_data: dict[str, Any]) -> tuple[Path, int]:
    """Generate a PDF report using ReportLab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
    except ImportError as exc:
        raise ValidationError("reportlab is not installed.") from exc

    _ensure_dir()
    path = _report_path(report_id, "pdf")
    doc = SimpleDocTemplate(str(path), pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=24, spaceAfter=12)
    h1_style = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=8)
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=6)
    body_style = styles["BodyText"]

    story = []

    # Cover page
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("InsightIQ", title_style))
    story.append(Paragraph(report_data.get("name", "Report"), h1_style))
    story.append(Paragraph(f"Report Type: {report_data.get('report_type', '').replace('_', ' ').title()}", body_style))
    story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", body_style))
    story.append(Paragraph(f"Dataset: {report_data.get('dataset_id', 'N/A')}", body_style))
    story.append(PageBreak())

    # Executive Summary
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.3 * cm))
    summary = report_data.get("executive_summary", {})
    if isinstance(summary, dict):
        for key, val in list(summary.items())[:10]:
            story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {val}", body_style))
    story.append(PageBreak())

    # KPIs
    kpis = report_data.get("kpis", {})
    if kpis:
        story.append(Paragraph("Key Performance Indicators", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.3 * cm))
        kpi_data = [["Metric", "Value"]]
        for k, v in list(kpis.items())[:20]:
            if not isinstance(v, (dict, list)):
                kpi_data.append([k.replace("_", " ").title(), str(v)])
        if len(kpi_data) > 1:
            t = Table(kpi_data, colWidths=[10 * cm, 6 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
        story.append(PageBreak())

    # Sections
    sections = ["customer", "revenue", "sales", "retention", "recommendations"]
    for section in sections:
        data = report_data.get(section)
        if not data or not isinstance(data, dict):
            continue
        story.append(Paragraph(section.replace("_", " ").title(), h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.3 * cm))
        for k, v in list(data.items())[:15]:
            if not isinstance(v, (dict, list)):
                story.append(Paragraph(f"<b>{k.replace('_', ' ').title()}:</b> {v}", body_style))
        story.append(PageBreak())

    # Metadata / Appendix
    story.append(Paragraph("Report Metadata", h1_style))
    story.append(Paragraph(f"Report ID: {report_id}", body_style))
    story.append(Paragraph(f"Generated at: {datetime.now(timezone.utc).isoformat()}", body_style))
    story.append(Paragraph(f"Platform: InsightIQ Enterprise", body_style))

    doc.build(story)
    size = path.stat().st_size
    logger.info("PDF report generated: %s (%d bytes)", path, size)
    return path, size


# ── Excel Generator ───────────────────────────────────────────────────────

def _generate_excel(report_id: str, report_data: dict[str, Any]) -> tuple[Path, int]:
    """Generate a multi-sheet Excel report using OpenPyXL."""
    _ensure_dir()
    path = _report_path(report_id, "xlsx")

    with pd.ExcelWriter(str(path), engine="openpyxl") as writer:
        # Summary sheet
        summary_rows = []
        for key, val in report_data.items():
            if not isinstance(val, (dict, list)):
                summary_rows.append({"Metric": key.replace("_", " ").title(), "Value": str(val)})
        if summary_rows:
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Summary", index=False)

        # KPIs sheet
        kpis = report_data.get("kpis", {})
        if isinstance(kpis, dict):
            kpi_rows = [{"KPI": k.replace("_", " ").title(), "Value": v} for k, v in kpis.items() if not isinstance(v, (dict, list))]
            if kpi_rows:
                pd.DataFrame(kpi_rows).to_excel(writer, sheet_name="KPIs", index=False)

        # Per-section sheets
        for section in ["customer", "revenue", "sales", "retention", "recommendations"]:
            data = report_data.get(section)
            if isinstance(data, dict):
                rows = [{"Metric": k.replace("_", " ").title(), "Value": str(v)} for k, v in data.items() if not isinstance(v, (dict, list))]
                if rows:
                    pd.DataFrame(rows).to_excel(writer, sheet_name=section[:31].title(), index=False)
            elif isinstance(data, list) and data:
                try:
                    pd.DataFrame(data).to_excel(writer, sheet_name=section[:31].title(), index=False)
                except Exception:
                    pass

        # Metadata sheet
        meta = pd.DataFrame([
            {"Field": "Report ID", "Value": report_id},
            {"Field": "Generated At", "Value": datetime.now(timezone.utc).isoformat()},
            {"Field": "Platform", "Value": "InsightIQ Enterprise"},
        ])
        meta.to_excel(writer, sheet_name="Metadata", index=False)

    # Force the workbook to close before returning to avoid resource warnings on Windows.
    import gc
    gc.collect()

    size = path.stat().st_size
    logger.info("Excel report generated: %s (%d bytes)", path, size)
    return path, size


# ── CSV Generator ─────────────────────────────────────────────────────────

def _generate_csv(report_id: str, report_data: dict[str, Any]) -> tuple[Path, int]:
    """Generate a flat CSV report."""
    _ensure_dir()
    path = _report_path(report_id, "csv")
    rows = []
    for section, data in report_data.items():
        if isinstance(data, dict):
            for k, v in data.items():
                if not isinstance(v, (dict, list)):
                    rows.append({"section": section, "metric": k, "value": str(v)})
        elif not isinstance(data, (dict, list)):
            rows.append({"section": "root", "metric": section, "value": str(data)})
    pd.DataFrame(rows).to_csv(str(path), index=False)
    size = path.stat().st_size
    return path, size


# ── JSON Generator ────────────────────────────────────────────────────────

def _generate_json(report_id: str, report_data: dict[str, Any]) -> tuple[Path, int]:
    """Generate a structured JSON report."""
    _ensure_dir()
    path = _report_path(report_id, "json")
    output = {
        "report_id": report_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": "InsightIQ Enterprise",
        "data": report_data,
    }
    path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    size = path.stat().st_size
    return path, size


# ── Dispatcher ────────────────────────────────────────────────────────────

_GENERATORS = {
    "pdf": _generate_pdf,
    "excel": _generate_excel,
    "xlsx": _generate_excel,
    "csv": _generate_csv,
    "json": _generate_json,
}


def generate_report(
    report_id: str,
    report_data: dict[str, Any],
    fmt: str,
) -> tuple[Path, int, float]:
    """
    Generate a report file in the requested format.

    Returns:
        Tuple of (file_path, file_size_bytes, duration_ms).
    """
    generator = _GENERATORS.get(fmt)
    if not generator:
        raise ValidationError(f"Unsupported report format: {fmt}")
    start = time.perf_counter()
    path, size = generator(report_id, report_data)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    return path, size, duration_ms
