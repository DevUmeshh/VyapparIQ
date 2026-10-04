import pandas as pd

from analytics import build_ai_summary, build_analysis, calculate_average_weekday_revenue, calculate_category_revenue, calculate_total_revenue, calculate_revenue_trend


def sample_frame():
    return pd.DataFrame({
        "Date": pd.to_datetime(["2026-09-01", "2026-09-02", "2026-09-08", "2026-09-09"]),
        "Item_Name": ["Rice", "Milk", "Rice", "Milk"],
        "Category": ["Grocery", "Dairy", "Grocery", "Dairy"],
        "Amount_INR": [100, 50, 200, 60],
    })


def test_revenue_and_category_metrics():
    data = sample_frame()
    assert calculate_total_revenue(data) == 410
    assert calculate_category_revenue(data).to_dict() == {"Grocery": 300, "Dairy": 110}
    assert build_analysis(data)["transaction_count"] == 4


def test_weekday_average_is_per_occurrence():
    averages = calculate_average_weekday_revenue(sample_frame())
    assert averages["Tuesday"] == 150
    assert averages["Wednesday"] == 55


def test_trend_and_ai_summary_are_aggregate_only():
    data = sample_frame()
    analysis = build_analysis(data)
    trend = calculate_revenue_trend(data)
    summary = build_ai_summary(analysis)
    assert trend["label"] in {"Increasing", "Decreasing", "Stable"}
    assert "Item_Name" not in summary
    assert summary["transactions"] == 4