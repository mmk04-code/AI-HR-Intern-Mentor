"""
Configuration & Credentials Management Module.
Safely detects and maps environment variables from .env files or directories
without ever printing, logging, or exposing secret keys.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

_LOADED = False


def _clean_val(val: Optional[str]) -> Optional[str]:
    """Clean surrounding quotes and whitespace from an env value."""
    if val is None:
        return None
    val = val.strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1].strip()
    return val if val else None


def load_project_env() -> None:
    """
    Search and safely load environment files without exposing keys.
    Supports .env as a file, or .env as a directory containing key files (e.g. .env/api_key).
    """
    global _LOADED
    if _LOADED:
        return

    base_dir = Path(__file__).resolve().parent.parent

    # 1. Check if .env is a directory
    env_dir = base_dir / ".env"
    if env_dir.is_dir():
        for child in env_dir.iterdir():
            if child.is_file():
                load_dotenv(dotenv_path=child, override=False)

    # 2. Check if .env is a regular file
    env_file = base_dir / ".env"
    if env_file.is_file():
        load_dotenv(dotenv_path=env_file, override=False)

    # 3. Fallback standard load_dotenv
    load_dotenv(override=False)

    _LOADED = True


# Initialize immediately upon import
load_project_env()


def get_primary_gemini_key() -> Optional[str]:
    """Retrieve primary Gemini API key across common aliases."""
    load_project_env()
    for alias in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_KEY"]:
        val = _clean_val(os.getenv(alias))
        if val:
            return val
    return None


def get_secondary_gemini_key() -> Optional[str]:
    """Retrieve optional secondary Gemini API key across common aliases."""
    load_project_env()
    for alias in ["GEMINI_API_KEY_2", "GEMINI_API_KEY2", "GEMINI_SECONDARY_KEY", "GOOGLE_API_KEY_2"]:
        val = _clean_val(os.getenv(alias))
        if val:
            return val
    return None


def get_openai_key() -> Optional[str]:
    """Retrieve optional OpenAI API key across common aliases."""
    load_project_env()
    for alias in ["OPENAI_API_KEY", "Open_AI_KEY", "OPENAI_KEY"]:
        val = _clean_val(os.getenv(alias))
        if val:
            return val
    return None


def get_gemini_model() -> str:
    """Retrieve configured Gemini model name."""
    load_project_env()
    return _clean_val(os.getenv("GEMINI_MODEL")) or "gemini-2.0-flash"


def get_openai_model() -> str:
    """Retrieve configured OpenAI model name."""
    load_project_env()
    return _clean_val(os.getenv("OPENAI_MODEL")) or "gpt-4o-mini"


def has_gemini_configured() -> bool:
    """Check if primary Gemini key is available (Boolean only, no secrets)."""
    return bool(get_primary_gemini_key())


def has_secondary_gemini_configured() -> bool:
    """Check if secondary Gemini key is available (Boolean only, no secrets)."""
    return bool(get_secondary_gemini_key())


def has_openai_configured() -> bool:
    """Check if OpenAI key is available (Boolean only, no secrets)."""
    return bool(get_openai_key())
