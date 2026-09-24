"""Runtime authentication settings loaded from environment variables."""

import os
from datetime import timedelta

SESSION_COOKIE_NAME = "vitta_one_session"
_SESSION_TTL_ENV = "VITTA_ONE_SESSION_TTL_SECONDS"
_COOKIE_SECURE_ENV = "VITTA_ONE_COOKIE_SECURE"


def session_ttl_seconds() -> int:
    """Return the explicitly configured positive server-session lifetime."""
    raw_value = os.getenv(_SESSION_TTL_ENV, "").strip()
    if not raw_value:
        raise RuntimeError(f"{_SESSION_TTL_ENV} deve ser definida com um inteiro positivo.")
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{_SESSION_TTL_ENV} deve ser um inteiro positivo.") from exc
    if value <= 0:
        raise RuntimeError(f"{_SESSION_TTL_ENV} deve ser um inteiro positivo.")
    return value


def session_ttl() -> timedelta:
    """Return the configured server-session lifetime."""
    return timedelta(seconds=session_ttl_seconds())


def secure_cookie_enabled() -> bool:
    """Return whether the browser session cookie must be restricted to HTTPS."""
    raw_value = os.getenv(_COOKIE_SECURE_ENV, "true").strip().casefold()
    if raw_value in {"1", "true", "yes", "on"}:
        return True
    if raw_value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(
        f"{_COOKIE_SECURE_ENV} deve ser true/false (ou equivalente booleano)."
    )
