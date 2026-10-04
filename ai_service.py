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


def get_openrouter_client(api_key: str | None = None) -> Any:
    """Create an OpenAI-compatible client only when a key is available."""
    from openai import OpenAI

    key = (api_key or config.get_api_key()).strip()
    if not key:
        raise ValueError("An OpenRouter API key is required for AI insights.")
    headers = {"HTTP-Referer": config.SITE_URL, "X-Title": config.SITE_NAME}
    headers = {key: value for key, value in headers.items() if value}
    return OpenAI(base_url=config.API_BASE_URL, api_key=key, default_headers=headers or None, timeout=config.REQUEST_TIMEOUT_SECONDS)


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
    client = get_openrouter_client(api_key)
    last_error: Exception | None = None
    models = [config.MODEL] + ([config.FALLBACK_MODEL] if config.FALLBACK_MODEL and config.FALLBACK_MODEL != config.MODEL else [])
    for model in models:
        for attempt in range(config.RETRY_COUNT + 1):
            try:
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_ai_prompt(summary, language)},
                ]
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.2,
                    )
                except Exception as structured_error:
                    # A few OpenRouter models do not advertise JSON mode. The prompt
                    # still requires JSON, which is validated before display.
                    if "response_format" not in str(structured_error).lower() and "json" not in str(structured_error).lower():
                        raise
                    response = client.chat.completions.create(model=model, messages=messages, temperature=0.2)
                content = response.choices[0].message.content or ""
                return validate_ai_response(content)
            except Exception as exc:
                last_error = exc
                if attempt < config.RETRY_COUNT:
                    time.sleep(0.5 * (attempt + 1))
    raise RuntimeError("AI insights are temporarily unavailable.") from last_error


def ask_followup_question(question: str, summary: dict[str, Any], language: str = "English", api_key: str | None = None) -> str:
    client = get_openrouter_client(api_key)
    response = client.chat.completions.create(
        model=config.MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + " Answer the user's question using only the summary. If it is not answerable, say you do not have enough information in this sales data to answer reliably."},
            {"role": "user", "content": build_ai_prompt(summary, language) + f"\nQuestion: {question[:500]}"},
        ],
        temperature=0.2,
    )
    return (response.choices[0].message.content or "I don't have enough information in this sales data to answer that reliably.").strip()