"""OpenRouter integration with structured validation and privacy boundaries."""

from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel, Field, ValidationError

import config


class Recommendation(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=1, max_length=500)
    action: str = Field(min_length=1, max_length=500)
    impact: str = Field(min_length=1, max_length=500)


class AIInsightResponse(BaseModel):
    business_health: str = Field(min_length=1, max_length=500)
    recommendations: list[Recommendation] = Field(min_length=3, max_length=3)


SYSTEM_PROMPT = """You are a practical business advisor for small Indian businesses.
Use only the aggregate business summary supplied by the application. Never invent or recalculate metrics,
profits, costs, customers, inventory, taxes, or statistics. Do not claim to be a Chartered Accountant.
Write concise, simple, practical advice in the requested language. Each recommendation must connect a real
signal to an action: what is happening, why it matters, and what to try. Return JSON only with exactly this shape:
{"business_health":"...","recommendations":[{"title":"...","reason":"...","action":"...","impact":"..."}]}
"""


def get_api_key(api_key: str | None = None) -> str:
    key = (api_key or config.get_api_key()).strip()
    if not key:
        raise ValueError("An OpenRouter API key is required for AI insights.")
    return key


def get_headers(api_key: str | None = None) -> dict[str, str]:
    key = get_api_key(api_key)
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if config.SITE_URL:
        headers["HTTP-Referer"] = config.SITE_URL
    if config.SITE_NAME:
        headers["X-Title"] = config.SITE_NAME
    return headers


def build_ai_prompt(summary: dict[str, Any], language: str = "English") -> str:
    return f"Language: {language}\nAggregate business summary (the only business data available):\n{json.dumps(summary, indent=2, default=str)}"


def parse_ai_response(content: str | dict[str, Any]) -> AIInsightResponse:
    """Parse JSON and enforce the exact three-recommendation contract."""
    if isinstance(content, dict):
        payload = content
    else:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            start, end = cleaned.find("{"), cleaned.rfind("}")
            if start < 0 or end <= start:
                raise
            payload = json.loads(cleaned[start : end + 1])
    return AIInsightResponse.model_validate(payload)


def validate_ai_response(content: str | dict[str, Any]) -> AIInsightResponse:
    try:
        return parse_ai_response(content)
    except (json.JSONDecodeError, TypeError, ValidationError, ValueError) as exc:
        raise ValueError("The AI response did not match the expected structure.") from exc


def request_ai_insights(summary: dict[str, Any], language: str = "English", api_key: str | None = None) -> AIInsightResponse:
    import requests

    headers = get_headers(api_key)
    url = f"{config.API_BASE_URL.rstrip('/')}/chat/completions"
    last_error: Exception | None = None
    models = [config.MODEL] + ([config.FALLBACK_MODEL] if config.FALLBACK_MODEL and config.FALLBACK_MODEL != config.MODEL else [])

    for model in models:
        for attempt in range(config.RETRY_COUNT + 1):
            try:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_ai_prompt(summary, language)},
                    ],
                    "temperature": 0.2,
                    "reasoning": {"enabled": True},
                }

                response = requests.post(
                    url=url,
                    headers=headers,
                    json=payload,
                    timeout=config.REQUEST_TIMEOUT_SECONDS,
                )

                if response.status_code == 401:
                    raise ValueError("The OpenRouter key could not be authenticated. Check your API key.")
                if response.status_code == 429:
                    raise RuntimeError("OpenRouter rate limits are active. Please try again shortly.")

                if response.status_code != 200:
                    try:
                        err_msg = response.json().get("error", {}).get("message", response.text)
                    except Exception:
                        err_msg = response.text
                    raise RuntimeError(f"OpenRouter API error ({response.status_code}): {err_msg}")

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise ValueError("No choices returned from OpenRouter.")

                content = choices[0].get("message", {}).get("content") or ""
                return validate_ai_response(content)
            except Exception as exc:
                last_error = exc
                if attempt < config.RETRY_COUNT:
                    time.sleep(0.5 * (attempt + 1))
    raise RuntimeError("AI insights are temporarily unavailable.") from last_error


def ask_followup_question(question: str, summary: dict[str, Any], language: str = "English", api_key: str | None = None) -> str:
    import requests

    headers = get_headers(api_key)
    url = f"{config.API_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": config.MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT + " Answer the user's question using only the summary. If it is not answerable, say you do not have enough information in this sales data to answer reliably."},
            {"role": "user", "content": build_ai_prompt(summary, language) + f"\nQuestion: {question[:500]}"},
        ],
        "temperature": 0.2,
        "reasoning": {"enabled": True},
    }

    response = requests.post(
        url=url,
        headers=headers,
        json=payload,
        timeout=config.REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code != 200:
        try:
            err_msg = response.json().get("error", {}).get("message", response.text)
        except Exception:
            err_msg = response.text
        raise RuntimeError(f"OpenRouter API error ({response.status_code}): {err_msg}")

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        return "I don't have enough information in this sales data to answer that reliably."

    content = choices[0].get("message", {}).get("content") or ""
    return (content or "I don't have enough information in this sales data to answer that reliably.").strip()