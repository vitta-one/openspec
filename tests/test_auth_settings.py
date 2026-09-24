"""Unit tests for authentication runtime settings."""

import pytest

from vitta_one.auth.settings import secure_cookie_enabled, session_ttl_seconds


def test_session_ttl_requires_explicit_positive_integer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VITTA_ONE_SESSION_TTL_SECONDS", raising=False)
    with pytest.raises(RuntimeError):
        session_ttl_seconds()

    monkeypatch.setenv("VITTA_ONE_SESSION_TTL_SECONDS", "3600")
    assert session_ttl_seconds() == 3600

    monkeypatch.setenv("VITTA_ONE_SESSION_TTL_SECONDS", "0")
    with pytest.raises(RuntimeError):
        session_ttl_seconds()


def test_cookie_secure_defaults_true_and_can_be_disabled_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VITTA_ONE_COOKIE_SECURE", raising=False)
    assert secure_cookie_enabled() is True

    monkeypatch.setenv("VITTA_ONE_COOKIE_SECURE", "false")
    assert secure_cookie_enabled() is False

    monkeypatch.setenv("VITTA_ONE_COOKIE_SECURE", "invalido")
    with pytest.raises(RuntimeError):
        secure_cookie_enabled()
