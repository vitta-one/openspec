"""Browser launcher for CI's bundled Chromium or a local system Chrome."""

import os
import re
import shutil
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url


def validate_loopback_base_url(value: str) -> str:
    """Never let browser QA send its synthetic login password to a remote host."""
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("QA_BASE_URL precisa apontar apenas para um host HTTP local")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("QA_BASE_URL possui uma porta inválida") from exc
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("QA_BASE_URL possui uma porta inválida")
    return value.rstrip("/")


def validate_disposable_database_url(
    raw_url: str,
    *,
    enabled: str,
    database_id: str,
) -> None:
    """Require the dedicated port and explicit container ID for visual captures."""
    try:
        url = make_url(raw_url)
    except Exception as exc:
        raise RuntimeError("Capturas recusadas: DATABASE_URL inválida") from exc
    if (
        enabled != "yes"
        or database_id != "vitta-one-operational-ui-qa-db"
        or url.drivername != "postgresql+psycopg"
        or url.host not in {"localhost", "127.0.0.1"}
        or url.port != 15432
        # Keep the workflow database and fresh local QA databases side by side.
        # Repeat runs must never inherit appointments or provider records.
        or not (
            url.database == "vitta_one"
            or re.fullmatch(r"vitta_one_operational_ui_qa(?:_[2-9]|_[1-9][0-9]+)?", url.database)
        )
        or url.username != "postgres"
    ):
        raise RuntimeError("Capturas recusadas: DATABASE_URL não identifica o PostgreSQL QA descartável")


def launch_chromium(playwright):
    """Use system Chrome only when explicitly requested for local QA."""
    options = {"headless": True}
    if os.environ.get("VITTA_ONE_USE_SYSTEM_CHROME") == "yes":
        if not shutil.which("google-chrome"):
            raise RuntimeError("VITTA_ONE_USE_SYSTEM_CHROME=yes, mas Chrome não está disponível")
        options["channel"] = "chrome"
    return playwright.chromium.launch(**options)
