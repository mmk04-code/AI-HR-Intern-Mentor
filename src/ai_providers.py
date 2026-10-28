"""
src/ai_providers.py — Unified Resilient AI Provider Engine.
Manages Google Gemini (primary and secondary keys) and OpenAI providers.
Features:
- Transient error classification with exponential backoff (rate limits, timeouts, 503s).
- Non-retry of permanent errors (401 auth failures, 404 missing models).
- Independent verification of primary and secondary Gemini keys.
- Zero secret exposure in logs or error messages.
- Clean error surfacing without silent hardcoded fake responses.
"""

import time
import logging
import re
from typing import Optional, Dict, Any, Tuple, List
from src.config import (
    get_primary_gemini_key,
    get_secondary_gemini_key,
    get_openai_key,
    get_gemini_model,
    get_openai_model
)

logger = logging.getLogger(__name__)


def _safe_error_message(error: Exception, *secrets: Optional[str]) -> str:
    """Return a short provider error with configured credentials redacted."""
    message = str(error)
    known_secrets = [
        get_primary_gemini_key(), get_secondary_gemini_key(), get_openai_key(), *secrets
    ]
    for secret in known_secrets:
        if secret:
            message = message.replace(secret, "[REDACTED]")
    message = re.sub(r"(?i)([?&](?:key|api_key)=)[^&\s]+", r"\1[REDACTED]", message)
    message = re.sub(r"(?i)(bearer\s+)[^\s,;]+", r"\1[REDACTED]", message)
    return message[:200]

# Transient error signatures suitable for single-retry with backoff
TRANSIENT_SIGNATURES = [
    "429", "quota", "resource_exhausted", "resourceexhausted",
    "timeout", "timed out", "503", "500", "overloaded", "unavailable",
    "deadline_exceeded", "temporary"
]

# Permanent error signatures that should fail fast without retry
PERMANENT_SIGNATURES = [
    "api_key_invalid", "invalid_api_key", "401", "403",
    "permission_denied", "permissiondenied", "not_found", "404",
    "model_not_found"
]


def classify_error(err_text: str) -> str:
    """Classify an error string as 'transient', 'permanent', or 'unknown'."""
    lower = err_text.lower()
    if any(sig in lower for sig in PERMANENT_SIGNATURES):
        return "permanent"
    if any(sig in lower for sig in TRANSIENT_SIGNATURES):
        return "transient"
    return "unknown"


class GeminiProvider:
    """Standalone Google Gemini provider supporting primary and secondary keys."""

    @staticmethod
    def _create_client(api_key: str):
        """Create a client using google.genai or fallback to google.generativeai."""
        try:
            from google import genai
            return ("google.genai", genai.Client(api_key=api_key))
        except ImportError:
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=api_key)
                return ("google.generativeai", legacy_genai)
            except ImportError:
                return (None, None)

    @classmethod
    def test_connection(cls, api_key: str, model_name: str) -> Tuple[bool, str]:
        """Test a Gemini key with a minimal request to verify validity and quota."""
        if not api_key:
            return False, "No Gemini API key provided."

        sdk_type, client = cls._create_client(api_key)
        if not sdk_type:
            return False, "Neither 'google-genai' nor 'google-generativeai' SDK is installed."

        try:
            if sdk_type == "google.genai":
                resp = client.models.generate_content(
                    model=model_name,
                    contents="Reply with: OK"
                )
                text = getattr(resp, "text", "") or ""
                if text.strip():
                    return True, f"Gemini connection verified ({model_name})."
                return False, f"Gemini returned an empty response ({model_name})."
            else:
                model = client.GenerativeModel(model_name)
                resp = model.generate_content("Reply with: OK")
                text = getattr(resp, "text", "") or ""
                if text.strip():
                    return True, f"Gemini connection verified ({model_name})."
                return False, f"Gemini returned an empty response ({model_name})."
        except Exception as e:
            err_msg = _safe_error_message(e, api_key)
            return False, f"Gemini connection failed ({type(e).__name__}): {err_msg}"

    @classmethod
    def generate_content(
        cls,
        prompt: str,
        api_key: str,
        model_name: str,
        max_retries: int = 1
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Execute generation with controlled retry for transient errors.
        Returns: (success: bool, text_or_error: str, error_type: Optional[str])
        """
        sdk_type, client = cls._create_client(api_key)
        if not sdk_type:
            return False, "Google GenAI SDK is not installed in the environment.", "sdk_missing"

        last_error = ""
        for attempt in range(max_retries + 1):
            try:
                if sdk_type == "google.genai":
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    text = getattr(response, "text", None)
                    if text and text.strip():
                        return True, text.strip(), None
                    return False, "Gemini returned an empty response.", "empty_response"
                else:
                    model = client.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    text = getattr(response, "text", None)
                    if text and text.strip():
                        return True, text.strip(), None
                    return False, "Gemini returned an empty response.", "empty_response"
            except Exception as exc:
                err_str = str(exc)
                err_class = classify_error(err_str)
                last_error = _safe_error_message(exc, api_key)

                # Do not retry permanent errors (invalid key, missing model)
                if err_class == "permanent":
                    return False, f"Gemini permanent error: {_safe_error_message(exc, api_key)}", "permanent"

                if attempt < max_retries and err_class == "transient":
                    time.sleep(1.0 * (attempt + 1))
                    continue

                return False, f"Gemini error: {_safe_error_message(exc, api_key)}", err_class

        return False, last_error or "Gemini call failed.", "unknown"


class OpenAIProvider:
    """Standalone OpenAI provider."""

    @staticmethod
    def test_connection(api_key: str, model_name: str) -> Tuple[bool, str]:
        """Test OpenAI API key connectivity with a lightweight completion."""
        if not api_key:
            return False, "No OpenAI API key provided."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, timeout=10.0)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Reply with: OK"}],
                max_tokens=5
            )
            return True, f"OpenAI connection verified ({model_name})."
        except ImportError:
            return False, "OpenAI SDK is not installed."
        except Exception as e:
            return False, f"OpenAI connection failed ({type(e).__name__}): {_safe_error_message(e, api_key)}"

    @classmethod
    def generate_content(
        cls,
        prompt: str,
        api_key: str,
        model_name: str,
        max_retries: int = 1
    ) -> Tuple[bool, str, Optional[str]]:
        """Execute OpenAI generation with retry handling."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, timeout=15.0)
        except ImportError:
            return False, "OpenAI SDK is not installed.", "sdk_missing"

        last_error = ""
        for attempt in range(max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                choice = response.choices[0] if response.choices else None
                if choice and choice.message and choice.message.content:
                    return True, choice.message.content.strip(), None
                return False, "OpenAI returned an empty response.", "empty_response"
            except Exception as exc:
                err_str = str(exc)
                err_class = classify_error(err_str)
                last_error = _safe_error_message(exc, api_key)

                if err_class == "permanent":
                    return False, f"OpenAI permanent error: {_safe_error_message(exc, api_key)}", "permanent"

                if attempt < max_retries and err_class == "transient":
                    time.sleep(1.0 * (attempt + 1))
                    continue

                return False, f"OpenAI error: {_safe_error_message(exc, api_key)}", err_class

        return False, last_error or "OpenAI call failed.", "unknown"


class AIProviderService:
    """
    Coordinating AI service executing provider failover chain:
    Primary Gemini -> Secondary Gemini -> OpenAI -> Honest failure reporting.
    """

    @classmethod
    def generate_text(
        cls,
        prompt: str,
        preferred_provider: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate text using available providers in priority order.
        Returns detailed dict with success status, provider name, and error trail.
        """
        errors: List[str] = []

        # 1. Primary Gemini
        gemini_model = get_gemini_model()
        primary_key = get_primary_gemini_key()
        if primary_key and preferred_provider in ("auto", "gemini"):
            success, result, err_type = GeminiProvider.generate_content(
                prompt=prompt,
                api_key=primary_key,
                model_name=gemini_model
            )
            if success:
                return {
                    "success": True,
                    "provider": "Gemini (Primary)",
                    "model": gemini_model,
                    "text": result,
                    "errors": []
                }
            errors.append(f"Primary Gemini ({gemini_model}): {result}")

        # 2. Secondary Gemini (if primary failed or unavailable)
        secondary_key = get_secondary_gemini_key()
        if secondary_key and preferred_provider in ("auto", "gemini"):
            success, result, err_type = GeminiProvider.generate_content(
                prompt=prompt,
                api_key=secondary_key,
                model_name=gemini_model
            )
            if success:
                return {
                    "success": True,
                    "provider": "Gemini (Secondary)",
                    "model": gemini_model,
                    "text": result,
                    "errors": errors
                }
            errors.append(f"Secondary Gemini ({gemini_model}): {result}")

        # 3. OpenAI
        openai_key = get_openai_key()
        openai_model = get_openai_model()
        if openai_key and preferred_provider in ("auto", "openai"):
            success, result, err_type = OpenAIProvider.generate_content(
                prompt=prompt,
                api_key=openai_key,
                model_name=openai_model
            )
            if success:
                return {
                    "success": True,
                    "provider": "OpenAI",
                    "model": openai_model,
                    "text": result,
                    "errors": errors
                }
            errors.append(f"OpenAI ({openai_model}): {result}")

        # All providers failed or none configured
        if not errors:
            errors.append("No active AI provider configured (GEMINI_API_KEY or OPENAI_API_KEY).")

        return {
            "success": False,
            "provider": None,
            "model": None,
            "text": "",
            "errors": errors
        }

    @classmethod
    def get_status_summary(cls) -> Dict[str, Any]:
        """Summarize configured providers without exposing keys."""
        primary_k = bool(get_primary_gemini_key())
        secondary_k = bool(get_secondary_gemini_key())
        openai_k = bool(get_openai_key())

        is_online = primary_k or secondary_k or openai_k

        return {
            "is_online": is_online,
            "primary_gemini_configured": primary_k,
            "secondary_gemini_configured": secondary_k,
            "openai_configured": openai_k,
            "gemini_model": get_gemini_model(),
            "openai_model": get_openai_model(),
            "status_label": "Configured (connection unverified)" if is_online else "Offline (limited rule-based / local reference mode)"
        }

