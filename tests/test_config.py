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
