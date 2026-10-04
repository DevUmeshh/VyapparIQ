"""VyapaarIQ Streamlit application entry point."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

import ai_service
from analytics import build_ai_summary, build_analysis, calculate_daily_revenue
from recommendations import generate_local_recommendations
from report import build_pdf_report, build_summary_csv
from ui import inject_styles, render_ai_insights, render_business_signals, render_charts, render_empty_state, render_footer, render_header, render_metrics, render_privacy_notice, render_upload_area
from validation import validate_and_clean_csv

ROOT = Path(__file__).parent
SAMPLE_PATH = ROOT / "data" / "dummy_sales.csv"
LANGUAGES = ["English", "Hinglish", "Hindi", "Marathi"]


def initialize_state() -> None:
    defaults = {"data": None, "analysis": None, "ai_result": None, "ai_fallback": False, "ai_error": "", "is_sample": False, "api_key": "", "language": "English", "chat": []}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def load_frame(frame: pd.DataFrame, is_sample: bool = False) -> None:
    result = validate_and_clean_csv(frame.to_csv(index=False).encode("utf-8"))
    if not result.valid:
        for error in result.errors:
            st.error(error)
        return
    analysis = build_analysis(result.cleaned_data)
    analysis["daily_revenue"] = calculate_daily_revenue(result.cleaned_data)
    st.session_state.update({"data": result.cleaned_data, "analysis": analysis, "ai_result": None, "ai_fallback": False, "ai_error": "", "is_sample": is_sample, "chat": []})
    st.session_state["validation"] = result


def clear_data() -> None:
    for key in ["data", "analysis", "ai_result", "validation"]:
        st.session_state[key] = None
    st.session_state.update({"ai_fallback": False, "ai_error": "", "is_sample": False, "chat": [], "api_key": ""})


def main() -> None:
    st.set_page_config(page_title="VyapaarIQ", page_icon="▦", layout="wide", initial_sidebar_state="collapsed")
    initialize_state()
    inject_styles()
    render_header()
    if st.session_state["analysis"] is None:
        render_empty_state()
        upload = render_upload_area()
        sample_col, download_col = st.columns([1, 1])
        with sample_col:
            if st.button("Try Sample Data", type="primary", use_container_width=True):
                load_frame(pd.read_csv(SAMPLE_PATH), is_sample=True)
                st.rerun()
        with download_col:
            st.download_button("Download Sample CSV", SAMPLE_PATH.read_bytes(), "vyapaar-iq-sample.csv", "text/csv", use_container_width=True)
        if upload is not None:
            result = validate_and_clean_csv(upload.getvalue())
            if result.valid:
                load_frame(result.cleaned_data)
                st.rerun()
            for error in result.errors:
                st.error(error)
        render_footer()
        return

    analysis = st.session_state["analysis"]
    if st.session_state["is_sample"]:
        st.caption("Sample Business · Local General Store")
    st.markdown('<div class="hero"><div class="eyebrow">Business Overview</div><h1>Your sales performance at a glance.</h1><p>Numbers are calculated locally from your cleaned sales data. Recommendations are based on the resulting business signals.</p></div>', unsafe_allow_html=True)
    render_metrics(analysis)
    st.markdown('<div class="section"><div class="eyebrow">Sales Performance</div><h2>Where your revenue is coming from.</h2></div>', unsafe_allow_html=True)
    render_charts(analysis)
    st.markdown('<div class="section"><div class="eyebrow">Business Signals</div><h2>Patterns worth paying attention to.</h2></div>', unsafe_allow_html=True)
    render_business_signals(analysis)

    st.markdown('<div class="section"><div class="eyebrow">VyapaarIQ Insights</div><h2>Practical actions based on your sales summary.</h2></div>', unsafe_allow_html=True)
    language = st.selectbox("Insight language", LANGUAGES, index=LANGUAGES.index(st.session_state["language"]), label_visibility="collapsed")
    st.session_state["language"] = language
    if st.session_state["ai_result"] is None:
        with st.expander("Optional OpenRouter key", expanded=False):
            st.caption("Keys are kept only in this session and are never included in reports or prompts.")
            st.session_state["api_key"] = st.text_input("OpenRouter API key", type="password", value=st.session_state["api_key"])
        if st.button("Generate AI insights", type="primary"):
            with st.spinner("Preparing your business summary..."):
                try:
                    st.session_state["ai_result"] = ai_service.request_ai_insights(build_ai_summary(analysis), language, st.session_state["api_key"] or None)
                except Exception as error:
                    st.session_state["ai_result"] = generate_local_recommendations(analysis)
                    st.session_state["ai_fallback"] = True
                    message = str(error).lower()
                    if "required for ai insights" in message:
                        st.session_state["ai_error"] = "No OpenRouter key is configured. Add a newly rotated key to .env or enter one in Optional OpenRouter key."
                    elif "api key" in message or "authentication" in message or "401" in message:
                        st.session_state["ai_error"] = "The OpenRouter key could not be authenticated. Check your .env key or enter a current key for this session."
                    elif "rate" in message or "429" in message:
                        st.session_state["ai_error"] = "OpenRouter rate limits are active. Local business signals are shown while the limit clears."
                    else:
                        st.session_state["ai_error"] = "The configured model did not return usable structured insights. Local business signals are shown instead."
            st.rerun()
    if st.session_state["ai_result"] is not None:
        if st.session_state["ai_error"]:
            st.caption(st.session_state["ai_error"])
        render_ai_insights(st.session_state["ai_result"], st.session_state["ai_fallback"])

    render_privacy_notice()
    with st.expander("View Sales Data"):
        validation = st.session_state.get("validation")
        if validation:
            st.caption(f"{validation.valid_rows:,} cleaned rows · {validation.categories_detected} categories · {validation.date_range}")
        st.dataframe(st.session_state["data"], use_container_width=True, hide_index=True)
        st.download_button("Download Cleaned CSV", st.session_state["data"].to_csv(index=False).encode("utf-8"), "vyapaar-iq-cleaned.csv", "text/csv")
    st.markdown('<div class="section"><div class="eyebrow">Exports</div><h2>Take the summary with you.</h2></div>', unsafe_allow_html=True)
    export_a, export_b, clear = st.columns(3)
    with export_a:
        st.download_button("Download Summary CSV", build_summary_csv(analysis), "vyapaar-iq-summary.csv", "text/csv", use_container_width=True)
    with export_b:
        st.download_button("Download Business Report", build_pdf_report(analysis, st.session_state["ai_result"] if not st.session_state["ai_fallback"] else None), "vyapaar-iq-report.pdf", "application/pdf", use_container_width=True)
    with clear:
        if st.button("Clear Data", use_container_width=True):
            clear_data()
            st.rerun()

    with st.expander("Ask VyapaarIQ"):
        for message in st.session_state["chat"]:
            st.chat_message(message["role"]).write(message["content"])
        question = st.text_input("Ask about your sales summary", placeholder="Which day should I focus on?")
        if st.button("Ask", disabled=not question.strip()):
            st.session_state["chat"].append({"role": "user", "content": question[:500]})
            try:
                answer = ai_service.ask_followup_question(question, build_ai_summary(analysis), language, st.session_state["api_key"] or None)
            except Exception:
                answer = "I don't have enough information in this sales data to answer that reliably."
            st.session_state["chat"].append({"role": "assistant", "content": answer})
            st.session_state["chat"] = st.session_state["chat"][-8:]
            st.rerun()
    render_footer()


if __name__ == "__main__":
    main()