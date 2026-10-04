"""Deterministic recommendations used when AI is unavailable and as a baseline."""

from __future__ import annotations

from typing import Any


def generate_local_recommendations(analysis: dict[str, Any]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    weakest = analysis.get("weakest_day", "Insufficient data")
    if weakest != "Insufficient data":
        recommendations.append({
            "title": f"Strengthen {weakest} sales",
            "reason": f"{weakest} has the lowest average revenue per weekday occurrence.",
            "action": f"Test one small {weakest} bundle or offer for two weeks and compare the next two {weakest}s.",
            "impact": "Creates a focused way to improve the weakest recurring sales signal.",
        })
    share = float(analysis.get("top_category_share", 0))
    category = analysis.get("top_category", "the leading category")
    if share >= 40:
        recommendations.append({
            "title": f"Protect {category} revenue",
            "reason": f"{category} contributes {share:.1f}% of recorded revenue.",
            "action": f"Monitor the key {category} products and test one complementary item to reduce over-dependence.",
            "impact": "Helps protect the strongest revenue source while broadening the mix.",
        })
    trend = analysis.get("trend", {})
    label = trend.get("label", "Insufficient data")
    if label == "Decreasing":
        recommendations.append({
            "title": "Review the weaker period",
            "reason": "The current period is below the comparison period.",
            "action": "Compare the weakest dates and test one operational change at a time.",
            "impact": "Makes a decline easier to diagnose without guessing at its cause.",
        })
    elif label == "Increasing":
        recommendations.append({
            "title": "Check whether growth holds",
            "reason": "The current period is above the comparison period.",
            "action": "Track the next two weeks against the current baseline before expanding the change.",
            "impact": "Separates sustained improvement from a short-term lift.",
        })
    else:
        recommendations.append({
            "title": "Improve one signal at a time",
            "reason": "Revenue is stable or there is not enough history for a strong trend call.",
            "action": f"Start with the weakest recurring day, {weakest}, and record the result of one small test.",
            "impact": "Keeps improvement measurable and practical.",
        })
    while len(recommendations) < 3:
        recommendations.append({
            "title": "Keep a weekly baseline",
            "reason": "A consistent baseline makes small changes easier to evaluate.",
            "action": "Review revenue, average bill, and category share at the end of each week.",
            "impact": "Supports clearer decisions from the next dataset refresh.",
        })
    return recommendations[:3]