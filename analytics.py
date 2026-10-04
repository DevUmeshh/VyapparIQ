"""Local, auditable business calculations."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def calculate_total_revenue(data: pd.DataFrame) -> float:
    return float(data["Amount_INR"].sum())


def calculate_transaction_count(data: pd.DataFrame) -> int:
    return int(len(data))


def calculate_average_transaction(data: pd.DataFrame) -> float:
    return calculate_total_revenue(data) / len(data) if len(data) else 0.0


def calculate_category_revenue(data: pd.DataFrame) -> pd.Series:
    return data.groupby("Category")["Amount_INR"].sum().sort_values(ascending=False)


def calculate_category_share(data: pd.DataFrame) -> pd.Series:
    revenue = calculate_category_revenue(data)
    total = revenue.sum()
    return revenue / total * 100 if total else revenue.astype(float)


def calculate_daily_revenue(data: pd.DataFrame) -> pd.Series:
    return data.groupby(data["Date"].dt.normalize())["Amount_INR"].sum().sort_index()


def calculate_weekday_revenue(data: pd.DataFrame) -> pd.Series:
    values = data.assign(Weekday=data["Date"].dt.day_name()).groupby("Weekday")["Amount_INR"].sum()
    return values.reindex([day for day in WEEKDAY_ORDER if day in values.index], fill_value=0)


def calculate_average_weekday_revenue(data: pd.DataFrame) -> pd.Series:
    working = data.assign(Weekday=data["Date"].dt.day_name())
    values = working.groupby("Weekday")["Amount_INR"].mean()
    return values.reindex([day for day in WEEKDAY_ORDER if day in values.index])


def calculate_best_sales_day(data: pd.DataFrame) -> str:
    values = calculate_average_weekday_revenue(data)
    return str(values.idxmax()) if not values.empty else "Insufficient data"


def calculate_weakest_sales_day(data: pd.DataFrame) -> str:
    values = calculate_average_weekday_revenue(data)
    return str(values.idxmin()) if not values.empty else "Insufficient data"


def calculate_highest_revenue_date(data: pd.DataFrame) -> str:
    values = calculate_daily_revenue(data)
    return values.idxmax().strftime("%d %b %Y") if not values.empty else "Insufficient data"


def calculate_lowest_revenue_date(data: pd.DataFrame) -> str:
    values = calculate_daily_revenue(data)
    return values.idxmin().strftime("%d %b %Y") if not values.empty else "Insufficient data"


def calculate_revenue_trend(data: pd.DataFrame) -> dict[str, Any]:
    daily = calculate_daily_revenue(data)
    if len(daily) < 4:
        return {"label": "Insufficient data", "change_percent": None, "confidence": "Insufficient data", "current": calculate_total_revenue(data), "previous": None}
    midpoint = len(daily) // 2
    previous = float(daily.iloc[:midpoint].sum())
    current = float(daily.iloc[midpoint:].sum())
    change = ((current - previous) / previous * 100) if previous else None
    if change is None or abs(change) < 3:
        label = "Stable"
    elif change > 0:
        label = "Increasing"
    else:
        label = "Decreasing"
    confidence = "High" if len(daily) >= 28 else "Medium" if len(daily) >= 10 else "Low"
    return {"label": label, "change_percent": change, "confidence": confidence, "current": current, "previous": previous}


def calculate_period_comparison(data: pd.DataFrame) -> dict[str, Any]:
    trend = calculate_revenue_trend(data)
    return {"previous_period": trend["previous"], "current_period": trend["current"], "change_percent": trend["change_percent"]}


def build_analysis(data: pd.DataFrame) -> dict[str, Any]:
    category_revenue = calculate_category_revenue(data)
    category_share = calculate_category_share(data)
    trend = calculate_revenue_trend(data)
    return {
        "total_revenue": calculate_total_revenue(data),
        "transaction_count": calculate_transaction_count(data),
        "average_transaction": calculate_average_transaction(data),
        "category_revenue": category_revenue,
        "category_share": category_share,
        "category_transaction_count": data.groupby("Category").size().sort_values(ascending=False),
        "top_category": str(category_revenue.index[0]) if not category_revenue.empty else "Insufficient data",
        "top_category_share": float(category_share.iloc[0]) if not category_share.empty else 0.0,
        "weekday_revenue": calculate_weekday_revenue(data),
        "average_weekday_revenue": calculate_average_weekday_revenue(data),
        "best_day": calculate_best_sales_day(data),
        "weakest_day": calculate_weakest_sales_day(data),
        "highest_revenue_date": calculate_highest_revenue_date(data),
        "lowest_revenue_date": calculate_lowest_revenue_date(data),
        "active_selling_days": int(data["Date"].dt.normalize().nunique()),
        "trend": trend,
        "has_quantity": "Quantity" in data.columns,
        "top_units_category": _top_units_category(data),
    }


def _top_units_category(data: pd.DataFrame) -> str | None:
    if "Quantity" not in data.columns:
        return None
    quantity = pd.to_numeric(data["Quantity"], errors="coerce")
    if quantity.notna().sum() == 0:
        return None
    return str(data.assign(_quantity=quantity).groupby("Category")["_quantity"].sum().idxmax())


def build_ai_summary(analysis: dict[str, Any]) -> dict[str, Any]:
    """Return only aggregate signals intended for the language model."""
    trend = analysis["trend"]
    return {
        "revenue_inr": round(analysis["total_revenue"], 2),
        "transactions": analysis["transaction_count"],
        "average_transaction_inr": round(analysis["average_transaction"], 2),
        "top_revenue_category": analysis["top_category"],
        "top_category_share_percent": round(analysis["top_category_share"], 2),
        "strongest_weekday": analysis["best_day"],
        "weakest_weekday": analysis["weakest_day"],
        "highest_revenue_date": analysis["highest_revenue_date"],
        "lowest_revenue_date": analysis["lowest_revenue_date"],
        "active_selling_days": analysis["active_selling_days"],
        "revenue_trend": trend["label"],
        "period_change_percent": round(trend["change_percent"], 2) if trend["change_percent"] is not None else None,
        "trend_confidence": trend["confidence"],
    }