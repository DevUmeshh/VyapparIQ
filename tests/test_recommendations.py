from recommendations import generate_local_recommendations


def test_recommendations_cover_weak_day_concentration_and_trend():
    analysis = {"weakest_day": "Tuesday", "top_category": "Grocery", "top_category_share": 55.0, "trend": {"label": "Decreasing"}}
    results = generate_local_recommendations(analysis)
    assert len(results) == 3
    assert "Tuesday" in results[0]["reason"]
    assert "Grocery" in results[1]["reason"]
    assert "comparison period" in results[2]["reason"]


def test_stable_data_gets_a_measurable_action():
    results = generate_local_recommendations({"weakest_day": "Monday", "top_category": "Dairy", "top_category_share": 20, "trend": {"label": "Stable"}})
    assert len(results) == 3
    assert "one small test" in results[1]["action"]