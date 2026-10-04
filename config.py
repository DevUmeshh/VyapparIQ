"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


APP_NAME = "VyapaarIQ"
TAGLINE = "Smart Insights for Every Business."
API_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it:free")
FALLBACK_MODEL = os.getenv("OPENROUTER_FALLBACK_MODEL", "google/gemma-3-27b-it:free").strip()
REQUEST_TIMEOUT_SECONDS = float(os.getenv("OPENROUTER_TIMEOUT", "30"))
RETRY_COUNT = max(0, min(2, int(os.getenv("OPENROUTER_RETRIES", "2"))))
MAX_UPLOAD_MB = max(1, int(os.getenv("MAX_UPLOAD_MB", "10")))
MAX_CHAT_MESSAGES = max(2, int(os.getenv("MAX_CHAT_MESSAGES", "8")))
SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", APP_NAME)


def get_api_key() -> str:
    """Read the API key without exposing it through application logs or reports."""
    try:
        import streamlit as st

        secret_key = st.secrets.get("OPENROUTER_API_KEY", "")
        if secret_key:
            return str(secret_key).strip()
    except Exception:
        pass
    return os.getenv("OPENROUTER_API_KEY", "").strip()