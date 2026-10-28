"""
tests/test_ai_providers.py — Tests for AIProviderService, GeminiProvider, and OpenAIProvider.
Validates error classification, failover logic, safe credential handling,
and honest error messaging without unhandled crashes.
"""

import pytest
from src.ai_providers import (
    classify_error,
    GeminiProvider,
    OpenAIProvider,
    AIProviderService
)


def test_error_classification():
    assert classify_error("429 Resource has been exhausted (e.g. check quota).") == "transient"
    assert classify_error("Request timed out after 10.0 seconds") == "transient"
    assert classify_error("503 Service Unavailable: server overloaded") == "transient"

    assert classify_error("API_KEY_INVALID: The provided key is invalid.") == "permanent"
    assert classify_error("401 Unauthorized: Invalid Authentication") == "permanent"
    assert classify_error("404 Not Found: models/unknown-model does not exist") == "permanent"

    assert classify_error("Something completely strange happened") == "unknown"


def test_status_summary_safe_booleans(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    summary = AIProviderService.get_status_summary()
    assert isinstance(summary["is_online"], bool)
    assert isinstance(summary["primary_gemini_configured"], bool)
    assert isinstance(summary["openai_configured"], bool)
    assert "api_key" not in summary  # Crucial: no exposed raw keys in summary
    assert "status_label" in summary


def test_generate_text_no_keys_configured(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY_2", raising=False)

    res = AIProviderService.generate_text("Hello test prompt")
    assert res["success"] is False
    assert res["provider"] is None
    assert len(res["errors"]) > 0
    assert any("No active AI provider configured" in e or "Gemini" in e for e in res["errors"])


def test_gemini_provider_test_connection_no_key():
    ok, msg = GeminiProvider.test_connection(api_key="", model_name="gemini-3.6-flash")
    assert ok is False
    assert "No Gemini API key provided" in msg


def test_openai_provider_test_connection_no_key():
    ok, msg = OpenAIProvider.test_connection(api_key="", model_name="gpt-4o-mini")
    assert ok is False
    assert "No OpenAI API key provided" in msg


@pytest.mark.live_api
def test_live_gemini_call_if_key_available():
    """Optional live test run only when real valid credentials are in the environment."""
    from src.config import get_primary_gemini_key, get_gemini_model
    key = get_primary_gemini_key()
    if not key:
        pytest.skip("No GEMINI_API_KEY present; skipping live API test.")

    ok, msg = GeminiProvider.test_connection(key, get_gemini_model())
    if not ok:
        pytest.skip(f"Live Gemini request not available in current network/quota: {msg}")
    assert ok is True

