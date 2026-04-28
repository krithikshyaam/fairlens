"""
core/reporter.py
Generates a PDF bias audit report using ReportLab.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from models.schemas import AnalysisResult, MitigationResult

# ── Colours ───────────────────────────────────────────────────────────────
BRAND_BLUE    = colors.HexColor("#1A56DB")
BRAND_DARK    = colors.HexColor("#111928")
BRAND_LIGHT   = colors.HexColor("#F3F4F6")
BRAND_GREEN   = colors.HexColor("#057A55")
BRAND_YELLOW  = colors.HexColor("#C27803")
BRAND_RED     = colors.HexColor("#C81E1E")
BRAND_BORDER  = colors.HexColor("#E5E7EB")


def _severity_color(severity: str):
    return {"low": BRAND_GREEN, "medium": BRAND_YELLOW, "high": BRAND_RED}.get(severity, BRAND_DARK)


def _build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=20,
                                 textColor=BRAND_DARK, spaceAfter=4, alignment=TA_LEFT),
        "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=11,
                                    textColor=colors.HexColor("#6B7280"), spaceAfter=12),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13,
                              textColor=BRAND_BLUE, spaceBefore=14, spaceAfter=4),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10,
                               textColor=BRAND_DARK, leading=15, spaceAfter=6),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=10,
                                 textColor=BRAND_DARK),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=9,
                                 textColor=colors.HexColor("#6B7280")),
    }
    return styles


def _metrics_table(metrics, styles, label="Fairness Metrics"):
    severity_col = _severity_color(metrics.bias_severity)

    data = [
        ["Metric", "Value", "Threshold", "Status"],
        ["Demographic Parity Difference",
         f"{metrics.demographic_parity_difference:.4f}", "< 0.10",
         "✓ PASS" if metrics.demographic_parity_difference < 0.10 else "✗ FAIL"],
        ["Equalized Odds Difference",
         f"{metrics.equalized_odds_difference:.4f}", "< 0.10",
         "✓ PASS" if metrics.equalized_odds_difference < 0.10 else "✗ FAIL"],
        ["Disparate Impact Ratio",
         f"{metrics.disparate_impact_ratio:.4f}", "> 0.80",
         "✓ PASS" if metrics.disparate_impact_ratio > 0.80 else "✗ FAIL"],
        ["Overall Model Accuracy",
         f"{metrics.overall_accuracy:.1%}", "—", "—"],
        ["Bias Severity",
         metrics.bias_severity.upper(), "—", "—"],
    ]

    col_widths = [7.5*cm, 3*cm, 3*cm, 3*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("ALIGN",      (0, 0), (-1, 0), "CENTER"),
        # Body
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("GRID",       (0, 0), (-1, -1), 0.5, BRAND_BORDER),
        ("ALIGN",      (1, 1), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _group_rates_table(group_positive_rates: dict, group_accuracies: dict):
    data = [["Group", "Positive Prediction Rate", "Accuracy"]]
    for g in sorted(group_positive_rates.keys()):
        data.append([
            g,
            f"{group_positive_rates[g]:.1%}",
            f"{group_accuracies.get(g, 0):.1%}",
        ])
    col_widths = [6*cm, 5*cm, 5.5*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("GRID",       (0, 0), (-1, -1), 0.5, BRAND_BORDER),
        ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def generate_pdf(
    analysis: AnalysisResult,
    mitigation: MitigationResult | None = None,
) -> bytes:
    """
    Generate a full bias audit PDF report.
    Returns raw PDF bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )
    styles = _build_styles()
    story = []

    # ── Header ────────────────────────────────────────────────────────────
    story.append(Paragraph("FairLens Bias Audit Report", styles["title"]))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')} | "
        f"Analysis ID: {analysis.analysis_id}",
        styles["subtitle"]
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_BLUE, spaceAfter=12))

    # ── Dataset Overview ──────────────────────────────────────────────────
    story.append(Paragraph("1. Dataset Overview", styles["h2"]))
    overview_data = [
        ["Dataset", analysis.dataset_name],
        ["Target Column", analysis.target_column],
        ["Protected Attributes", ", ".join(analysis.protected_attributes)],
        ["Rows", f"{analysis.data_profile.row_count:,}"],
        ["Columns", str(analysis.data_profile.column_count)],
        ["Model Used", analysis.model_type],
    ]
    ov_table = Table(overview_data, colWidths=[5*cm, 11.6*cm])
    ov_table.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("GRID",      (0, 0), (-1, -1), 0.5, BRAND_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(ov_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Fairness Metrics ──────────────────────────────────────────────────
    story.append(Paragraph("2. Fairness Metrics", styles["h2"]))
    story.append(_metrics_table(analysis.metrics, styles))
    story.append(Spacer(1, 0.4*cm))

    # ── Per-Group Breakdown ───────────────────────────────────────────────
    story.append(Paragraph("3. Per-Group Outcome Breakdown", styles["h2"]))
    story.append(_group_rates_table(
        analysis.metrics.group_positive_rates,
        analysis.metrics.group_accuracies
    ))
    story.append(Spacer(1, 0.4*cm))

    # ── Top Bias Drivers ──────────────────────────────────────────────────
    story.append(Paragraph("4. Top Bias-Driving Features (SHAP)", styles["h2"]))
    feat_data = [["Feature", "Mean |SHAP|", "Role"]]
    for fi in analysis.feature_importances[:10]:
        feat_data.append([fi.feature, f"{fi.shap_value:.6f}", fi.direction.replace("_", " ")])
    feat_table = Table(feat_data, colWidths=[7*cm, 4*cm, 5.6*cm], repeatRows=1)
    feat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("GRID",       (0, 0), (-1, -1), 0.5, BRAND_BORDER),
        ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(feat_table)
    story.append(Spacer(1, 0.4*cm))

    # ── AI Explanation ────────────────────────────────────────────────────
    if analysis.gemini_explanation:
        story.append(Paragraph("5. AI-Generated Explanation (Gemini)", styles["h2"]))
        story.append(Paragraph(analysis.gemini_explanation, styles["body"]))
        story.append(Spacer(1, 0.4*cm))

    # ── Mitigation Results (optional) ─────────────────────────────────────
    if mitigation:
        story.append(Paragraph("6. Mitigation Results", styles["h2"]))
        story.append(Paragraph(
            f"Strategy applied: <b>{mitigation.strategy}</b>", styles["body"]
        ))

        # Before vs After table
        comp_data = [
            ["Metric", "Before", "After", "Δ Change"],
        ]
        b, a = mitigation.before_metrics, mitigation.after_metrics
        rows = [
            ("Demographic Parity Difference",
             b.demographic_parity_difference, a.demographic_parity_difference),
            ("Equalized Odds Difference",
             b.equalized_odds_difference, a.equalized_odds_difference),
            ("Disparate Impact Ratio",
             b.disparate_impact_ratio, a.disparate_impact_ratio),
            ("Overall Accuracy",
             b.overall_accuracy, a.overall_accuracy),
        ]
        for name, bv, av in rows:
            delta = av - bv
            delta_str = f"+{delta:.4f}" if delta > 0 else f"{delta:.4f}"
            comp_data.append([name, f"{bv:.4f}", f"{av:.4f}", delta_str])

        comp_table = Table(comp_data, colWidths=[7.5*cm, 3*cm, 3*cm, 3*cm], repeatRows=1)
        comp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("GRID",       (0, 0), (-1, -1), 0.5, BRAND_BORDER),
            ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(comp_table)
        story.append(Spacer(1, 0.3*cm))

        if mitigation.gemini_explanation:
            story.append(Paragraph(mitigation.gemini_explanation, styles["body"]))

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Generated by FairLens — AI-Powered Bias Detection Platform",
        styles["small"]
    ))

    doc.build(story)
    return buf.getvalue()
