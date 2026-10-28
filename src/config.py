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
    """Clean surrounding quotes, whitespace, and newlines from an env value."""
    if val is None:
        return None
    val = val.strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1].strip()
    return val if val else None


def _clean_credential(val: Optional[str]) -> Optional[str]:
    """Treat common template values as unset instead of attempting API/SMTP calls."""
    value = _clean_val(val)
    if not value:
        return None
    normalized = value.lower()
    placeholders = {
        "gemini_api_key", "openai_api_key", "open_ai_api_key", "open_ai_key",
        "your_api_key_here", "your_gemini_api_key_here", "your_openai_api_key_here",
        "gmail_id", "gmail_password", "your_email@gmail.com", "your_app_password",
        "change_me", "changeme", "replace_me", "paste_api_key_here",
    }
    if normalized in placeholders or normalized.startswith(("your_", "replace_", "paste_")):
        return None
    if value.startswith("<") and value.endswith(">"):
        return None
    return value


def load_project_env() -> None:
    """
    Search and safely load environment files without exposing keys.
    Supports .env as a file, or .env as a directory containing key files (e.g. .env/api_key.txt, .env/email.txt).
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
                # First run standard dotenv loader in case it's KEY=VALUE
                load_dotenv(dotenv_path=child, override=False)

                child_name = child.name.lower()
                # Parse raw API key if present
                if "api_key" in child_name or child_name == "gemini_key":
                    try:
                        raw = child.read_text(encoding="utf-8").strip()
                        if raw:
                            if "=" in raw:
                                for line in raw.splitlines():
                                    if "=" in line:
                                        k, v = line.split("=", 1)
                                        os.environ.setdefault(k.strip(), _clean_val(v) or "")
                            else:
                                os.environ.setdefault("GEMINI_API_KEY", raw)
                    except OSError:
                        pass

                # Parse email settings if present
                elif "email" in child_name:
                    try:
                        lines = [l.strip() for l in child.read_text(encoding="utf-8").splitlines() if l.strip()]
                        for line in lines:
                            if "=" in line:
                                k, v = line.split("=", 1)
                                os.environ.setdefault(k.strip(), _clean_val(v) or "")
                            elif "@" in line and not os.getenv("SMTP_USERNAME"):
                                os.environ["SMTP_USERNAME"] = line
                                os.environ["EMAIL_USER"] = line
                            elif not os.getenv("SMTP_PASSWORD") and "@" not in line:
                                os.environ["SMTP_PASSWORD"] = line
                                os.environ["EMAIL_PASSWORD"] = line
                    except OSError:
                        pass

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
    """Retrieve primary Gemini API key across common aliases and secret files."""
    load_project_env()
    for alias in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_KEY"]:
        val = _clean_credential(os.getenv(alias))
        if val:
            return val

    # Secret-file checks
    base_dir = Path(__file__).resolve().parent.parent
    for key_file in (
        base_dir / ".env" / "api_key.txt",
        base_dir / ".env" / "api_key",
        base_dir / ".env" / "gemini" / "api_key"
    ):
        try:
            if key_file.is_file():
                raw = _clean_credential(key_file.read_text(encoding="utf-8"))
                if raw:
                    if "=" in raw:
                        for line in raw.splitlines():
                            if "=" in line:
                                k, v = line.split("=", 1)
                                if k.strip().upper() in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "KEY"):
                                    return _clean_credential(v)
                    return raw
        except OSError:
            continue
    return None


def get_secondary_gemini_key() -> Optional[str]:
    """Retrieve optional secondary Gemini API key across common aliases and files."""
    load_project_env()
    for alias in ["GEMINI_API_KEY_2", "GEMINI_API_KEY2", "GEMINI_SECONDARY_KEY", "GOOGLE_API_KEY_2"]:
        val = _clean_credential(os.getenv(alias))
        if val:
            return val

    base_dir = Path(__file__).resolve().parent.parent
    for key_file in (
        base_dir / ".env" / "api_key_2.txt",
        base_dir / ".env" / "secondary_api_key.txt",
        base_dir / ".env" / "gemini" / "api_key_2"
    ):
        try:
            if key_file.is_file():
                raw = _clean_credential(key_file.read_text(encoding="utf-8"))
                if raw:
                    return raw
        except OSError:
            continue
    return None


def get_openai_key() -> Optional[str]:
    """Retrieve optional OpenAI API key across common aliases and secret files."""
    load_project_env()
    for alias in ["OPENAI_API_KEY", "OPEN_AI_API_KEY", "Open_AI_KEY", "OPENAI_KEY"]:
        val = _clean_credential(os.getenv(alias))
        if val:
            return val

    base_dir = Path(__file__).resolve().parent.parent
    for key_file in (
        base_dir / ".env" / "open_ai" / "api_key",
        base_dir / "open_ai" / "api_key",
        base_dir / ".env" / "openai_key.txt"
    ):
        try:
            if key_file.is_file():
                value = _clean_credential(key_file.read_text(encoding="utf-8"))
                if value:
                    return value
        except OSError:
            continue
    return None


def get_gemini_model() -> str:
    """Retrieve configured Gemini model name."""
    load_project_env()
    return _clean_val(os.getenv("GEMINI_MODEL")) or "gemini-3.6-flash"


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


def get_email_credentials() -> Dict[str, Any]:
    """Retrieve SMTP / email credentials without exposing secrets."""
    load_project_env()
    port_value = os.getenv("SMTP_PORT")
    try:
        port = int(port_value) if port_value else 587
    except (TypeError, ValueError):
        port = 0
    host_value = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER")
    return {
        "server": _clean_credential(host_value) if host_value else "smtp.gmail.com",
        "port": port,
        "username": _clean_credential(os.getenv("SMTP_USER")) or _clean_credential(os.getenv("SMTP_USERNAME")) or _clean_credential(os.getenv("EMAIL_USER")) or "",
        "password": _clean_credential(os.getenv("SMTP_PASSWORD")) or _clean_credential(os.getenv("EMAIL_PASSWORD")) or "",
        "from_address": _clean_credential(os.getenv("SMTP_FROM")) or _clean_credential(os.getenv("SMTP_USER")) or "",
        "use_tls": os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"true", "1", "yes"},
    }


def has_email_configured() -> bool:
    """Check if email credentials are fully available."""
    creds = get_email_credentials()
    return bool(
        creds.get("server")
        and creds.get("username")
        and creds.get("password")
        and 1 <= creds.get("port", 0) <= 65535
    )
