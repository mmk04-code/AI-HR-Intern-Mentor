"""
Unit tests for src/config.py (Safe credentials and environment detection)
"""

import os
import pytest
from src.config import (
    _clean_val,
    get_primary_gemini_key,
    get_secondary_gemini_key,
    get_openai_key,
    get_gemini_model,
    get_openai_model,
    _clean_credential,
    get_email_credentials,
    has_email_configured,
    has_gemini_configured,
    has_openai_configured
)


def test_clean_val():
    assert _clean_val('  "secret-key-123"  ') == "secret-key-123"
    assert _clean_val(" 'another-key-456' ") == "another-key-456"
    assert _clean_val("unquoted-key") == "unquoted-key"
    assert _clean_val("") is None
    assert _clean_val(None) is None


def test_config_detection_boolean_only():
    # Verify boolean detection works without exposing actual values
    gemini_ready = has_gemini_configured()
    assert isinstance(gemini_ready, bool)

    openai_ready = has_openai_configured()
    assert isinstance(openai_ready, bool)

    # Models
    assert get_gemini_model() != ""
    assert get_openai_model() != ""


def test_alias_mapping(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_KEY", raising=False)
    assert get_primary_gemini_key() == "test-google-key"

    monkeypatch.setenv("GEMINI_API_KEY_2", "test-sec-key")
    assert get_secondary_gemini_key() == "test-sec-key"

    monkeypatch.setenv("Open_AI_KEY", "test-openai-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert get_openai_key() == "test-openai-key"

    monkeypatch.setenv("OPEN_AI_API_KEY", "test-openai-api-key")
    monkeypatch.delenv("Open_AI_KEY", raising=False)
    assert get_openai_key() == "test-openai-api-key"


def test_openai_model_can_be_configured(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test-model")
    assert get_openai_model() == "gpt-test-model"


def test_template_credentials_are_treated_as_missing():
    assert _clean_credential("GEMINI_API_KEY") is None
    assert _clean_credential("your_gemini_api_key_here") is None
    assert _clean_credential("gmail_password") is None


def test_smtp_user_alias_and_invalid_port(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_USER", "coordinator@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "actual-app-password")
    monkeypatch.setenv("SMTP_PORT", "bad-port")
    creds = get_email_credentials()
    assert creds["username"] == "coordinator@example.com"
    assert creds["port"] == 0
    assert has_email_configured() is False
