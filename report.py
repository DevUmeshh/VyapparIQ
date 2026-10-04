"""Downloadable report and aggregate summary exports."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def format_inr(value: float) -> str:
    value = float(value)
    sign = "-" if value < 0 else ""
    number = f"{abs(value):,.2f}".rstrip("0").rstrip(".")
    return f"{sign}₹{number}"


def build_summary_csv(analysis: dict) -> bytes:
    trend = analysis["trend"]
    rows = [
        ("Revenue", analysis["total_revenue"]),
        ("Transactions", analysis["transaction_count"]),
        ("Average Transaction", analysis["average_transaction"]),
        ("Top Revenue Category", analysis["top_category"]),
        ("Top Category Share (%)", analysis["top_category_share"]),
        ("Strongest Weekday", analysis["best_day"]),
        ("Weakest Weekday", analysis["weakest_day"]),
        ("Highest Revenue Date", analysis["highest_revenue_date"]),
        ("Lowest Revenue Date", analysis["lowest_revenue_date"]),
        ("Active Selling Days", analysis["active_selling_days"]),
        ("Revenue Trend", trend["label"]),
        ("Period Change (%)", trend["change_percent"]),
        ("Trend Confidence", trend["confidence"]),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"]).to_csv(index=False).encode("utf-8")


def build_pdf_report(analysis: dict, ai_result: object | None = None) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = [Paragraph("VyapaarIQ", styles["Title"]), Paragraph("Smart Insights for Every Business.", styles["Normal"]), Spacer(1, 8)]
    trend = analysis["trend"]
    values = [
        ["Metric", "Value"],
        ["Revenue", format_inr(analysis["total_revenue"])],
        ["Transactions", str(analysis["transaction_count"])],
        ["Average transaction", format_inr(analysis["average_transaction"])],
        ["Top revenue category", str(analysis["top_category"])],
        ["Top category share", f"{analysis['top_category_share']:.1f}%"],
        ["Strongest weekday", str(analysis["best_day"])],
        ["Weakest weekday", str(analysis["weakest_day"])],
        ["Revenue trend", f"{trend['label']} ({trend['confidence']} confidence)"],
    ]
    table = Table(values, colWidths=[65 * mm, 95 * mm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173f35")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d6ddd8")), ("PADDING", (0, 0), (-1, -1), 7)]))
    story.extend([table, Spacer(1, 10), Paragraph("Recommendations", styles["Heading2"])])
    recommendations = getattr(ai_result, "recommendations", []) if ai_result else []
    for index, recommendation in enumerate(recommendations, 1):
        story.append(Paragraph(f"{index}. {recommendation.title}: {recommendation.action}", styles["BodyText"]))
    story.extend([Spacer(1, 10), Paragraph("Methodology: Revenue and business signals are calculated locally from the cleaned CSV. Profit, tax, cash flow, and customer metrics are not inferred when those fields are unavailable.", styles["BodyText"]), Paragraph("Privacy: Detailed sales rows are processed by VyapaarIQ. The AI receives only an aggregated business summary for generating insights.", styles["BodyText"]), Paragraph("VyapaarIQ provides data-based business insights and is not a substitute for professional accounting or tax advice.", styles["BodyText"])])
    document.build(story)
    return output.getvalue()