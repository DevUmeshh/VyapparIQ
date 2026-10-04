import json

import pytest

from ai_service import validate_ai_response


def valid_payload():
    return {"business_health": "Revenue is stable.", "recommendations": [{"title": f"Test {i}", "reason": "A calculated signal matters.", "action": "Try one focused change.", "impact": "Makes the result measurable."} for i in range(3)]}


def test_structured_response_requires_exactly_three_recommendations():
    parsed = validate_ai_response(json.dumps(valid_payload()))
    assert len(parsed.recommendations) == 3


def test_malformed_response_is_rejected():
    with pytest.raises(ValueError):
        validate_ai_response("not json")


def test_wrong_recommendation_count_is_rejected():
    payload = valid_payload()
    payload["recommendations"] = payload["recommendations"][:2]
    with pytest.raises(ValueError):
        validate_ai_response(payload)