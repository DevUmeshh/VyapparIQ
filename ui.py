"""Reusable Streamlit presentation components."""

from __future__ import annotations

import html
from typing import Any

import plotly.express as px
import streamlit as st

from report import format_inr


def inject_styles() -> None:
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#17201d; --muted:#66716c; --green:#17634f; --pale:#eef4ef; --line:#dbe3dd; --paper:#fbfcfa; }
    .stApp { background:var(--paper); color:var(--ink); font-family:'DM Sans', sans-serif; }
    h1,h2,h3 { font-family:'Space Grotesk', sans-serif; letter-spacing:0; color:var(--ink); }
    .block-container { max-width:1320px; padding:2.2rem 4vw 3rem; }
    .brand { color:var(--green); font:700 1.35rem 'Space Grotesk',sans-serif; letter-spacing:0; }
    .eyebrow { text-transform:uppercase; color:var(--green); font-size:.72rem; font-weight:700; letter-spacing:.12em; }
    .muted { color:var(--muted); }
    .hero { border-bottom:1px solid var(--line); padding:1rem 0 2.6rem; margin-bottom:2rem; }
    .hero h1 { font-size:clamp(2.1rem,4vw,4.15rem); line-height:1.02; max-width:780px; margin:.55rem 0 .9rem; }
    .hero p { color:var(--muted); font-size:1.05rem; max-width:600px; }
    .section { border-top:1px solid var(--line); padding-top:1.45rem; margin-top:2.5rem; }
    .metric { border-top:3px solid var(--green); padding:1rem 0 1.1rem; min-height:100px; }
    .metric-label { color:var(--muted); font-size:.8rem; text-transform:uppercase; letter-spacing:.08em; }
    .metric-value { font:600 clamp(1.35rem,2.1vw,2rem) 'Space Grotesk', sans-serif; margin-top:.4rem; overflow-wrap:anywhere; }
    .signal { background:var(--pale); border-left:3px solid var(--green); padding:.9rem 1rem; min-height:92px; }
    .signal-label { color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; }
    .signal-value { font-weight:600; margin-top:.4rem; }
    .insight { border-top:1px solid var(--line); padding:1rem 0; }
    .insight-number { color:var(--green); font:700 1.15rem 'Space Grotesk',sans-serif; }
    .insight-title { font-weight:700; font-size:1.05rem; }
    .insight-copy { color:var(--muted); font-size:.9rem; margin-top:.25rem; }
    .privacy { background:#f1f5f1; border:1px solid var(--line); padding:.8rem 1rem; color:#4f5c56; font-size:.83rem; }
    .footer { border-top:1px solid var(--line); margin-top:3rem; padding-top:1rem; color:var(--muted); font-size:.78rem; }
    @media (max-width:700px) { .block-container { padding:1.3rem 1rem 2rem; } .hero { padding-bottom:1.7rem; } }
    </style>""", unsafe_allow_html=True)


def render_header() -> None:
    st.markdown('<div class="brand">VyapaarIQ</div>', unsafe_allow_html=True)


def render_empty_state() -> None:
    st.markdown('<div class="hero"><div class="eyebrow">Smart Insights for Every Business.</div><h1>Understand your business in minutes.</h1><p>Upload your sales data and VyapaarIQ will organize the numbers, show the important patterns, and suggest what to test next.</p></div>', unsafe_allow_html=True)
    st.markdown("""<div class="muted" style="margin-bottom:.8rem">A practical workspace for local retailers, vendors, and small businesses.</div>""", unsafe_allow_html=True)


def render_upload_area() -> Any:
    uploaded = st.file_uploader("Upload Sales CSV", type=["csv"], help="Expected fields: Date, Item_Name, Category, Amount_INR. Quantity is optional.")
    st.caption("Expected fields: Date · Item_Name · Category · Amount_INR")
    return uploaded


def render_metrics(analysis: dict[str, Any]) -> None:
    columns = st.columns(4)
    values = [("Revenue", format_inr(analysis["total_revenue"])), ("Transactions", f"{analysis['transaction_count']:,}"), ("Avg. Bill", format_inr(analysis["average_transaction"])), ("Top Category", analysis["top_category"])]
    for column, (label, value) in zip(columns, values):
        column.markdown(f'<div class="metric"><div class="metric-label">{html.escape(label)}</div><div class="metric-value">{html.escape(value)}</div></div>', unsafe_allow_html=True)


def render_charts(analysis: dict[str, Any]) -> None:
    left, right = st.columns(2)
    category = analysis["category_revenue"].rename_axis("Category").reset_index(name="Revenue")
    category["Revenue"] = category["Revenue"].round(2)
    figure = px.bar(category, x="Revenue", y="Category", orientation="h", text_auto=".2s", color_discrete_sequence=["#17634f"])
    figure.update_layout(height=360, margin=dict(l=0, r=10, t=25, b=0), title="Revenue by Category", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False, xaxis_title=None, yaxis_title=None, font=dict(family="DM Sans", color="#17201d"))
    figure.update_xaxes(tickprefix="₹", showgrid=True, gridcolor="#e7ece8")
    daily = analysis["daily_revenue"] if "daily_revenue" in analysis else None
    if daily is None:
        st.warning("Daily chart is unavailable for this dataset.")
    with left:
        st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
    if daily is not None:
        trend_figure = px.line(daily.rename_axis("Date").reset_index(name="Revenue"), x="Date", y="Revenue", markers=True, color_discrete_sequence=["#17634f"])
        trend_figure.update_layout(height=360, margin=dict(l=0, r=10, t=25, b=0), title="Daily Revenue Trend", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False, xaxis_title=None, yaxis_title=None, font=dict(family="DM Sans", color="#17201d"))
        trend_figure.update_yaxes(tickprefix="₹", showgrid=True, gridcolor="#e7ece8")
        with right:
            st.plotly_chart(trend_figure, use_container_width=True, config={"displayModeBar": False})


def render_business_signals(analysis: dict[str, Any]) -> None:
    trend = analysis["trend"]
    signals = [("Strongest day", analysis["best_day"]), ("Weakest day", analysis["weakest_day"]), ("Highest revenue date", analysis["highest_revenue_date"]), ("Active selling days", str(analysis["active_selling_days"]))]
    columns = st.columns(4)
    for column, (label, value) in zip(columns, signals):
        column.markdown(f'<div class="signal"><div class="signal-label">{html.escape(label)}</div><div class="signal-value">{html.escape(value)}</div></div>', unsafe_allow_html=True)
    change = trend["change_percent"]
    change_text = "Not available" if change is None else f"{change:+.2f}%"
    st.caption(f"Revenue trend: {trend['label']} · Trend confidence: {trend['confidence']} · Period change: {change_text}")


def render_ai_insights(result: Any, is_fallback: bool = False) -> None:
    if is_fallback:
        st.info("AI insights unavailable. Your sales analysis is still available below.")
        st.markdown("### Local Business Signals")
    else:
        st.markdown("### VyapaarIQ Insights")
        st.caption("Based on your sales summary")
    health = getattr(result, "business_health", "Local recommendations based on calculated business signals.")
    st.markdown(f"**Business Health**  \n{health}")
    for index, recommendation in enumerate(getattr(result, "recommendations", result), 1):
        st.markdown(f'<div class="insight"><span class="insight-number">{index:02d}</span>&nbsp;&nbsp;<span class="insight-title">{html.escape(recommendation.title if hasattr(recommendation, "title") else recommendation["title"])}</span><div class="insight-copy"><b>Why it matters</b><br>{html.escape(recommendation.reason if hasattr(recommendation, "reason") else recommendation["reason"])}<br><br><b>What to try</b><br>{html.escape(recommendation.action if hasattr(recommendation, "action") else recommendation["action"])}<br><br><b>Expected direction</b><br>{html.escape(recommendation.impact if hasattr(recommendation, "impact") else recommendation["impact"])}</div></div>', unsafe_allow_html=True)


def render_privacy_notice() -> None:
    st.markdown('<div class="privacy"><b>Privacy</b><br>Detailed sales rows are processed by VyapaarIQ. The AI receives only an aggregated business summary for generating insights.</div>', unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown('<div class="footer">VyapaarIQ provides data-based business insights and is not a substitute for professional accounting or tax advice.</div>', unsafe_allow_html=True)