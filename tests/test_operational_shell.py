"""Presentation defaults that must remain aligned with the role references."""
import importlib

import pytest

from vitta_one.auth.roles import Role


def _components_with_valid_session_config(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("VITTA_ONE_SESSION_TTL_SECONDS", "3600")
    return importlib.import_module("vitta_one.ui.components")


def test_sidebar_default_is_compact_for_operational_reception_admin_and_finance(monkeypatch):
    components = _components_with_valid_session_config(monkeypatch)
    default_open = getattr(components, "_sidebar_expanded_by_default", None)

    assert callable(default_open)
    assert default_open(Role.RECEPCIONISTA) is False
    assert default_open(Role.ADMINISTRADOR) is False
    assert default_open(Role.FINANCEIRO) is False


def test_sidebar_default_preserves_expanded_medical_and_patient_navigation(monkeypatch):
    components = _components_with_valid_session_config(monkeypatch)
    default_open = getattr(components, "_sidebar_expanded_by_default", None)

    assert callable(default_open)
    assert default_open(Role.MEDICO) is True
    assert default_open(Role.PACIENTE) is True


def test_visual_qa_guards_reject_remote_hosts_and_non_disposable_databases():
    from qa_browser.playwright_support import (
        validate_disposable_database_url,
        validate_loopback_base_url,
    )

    assert validate_loopback_base_url("http://127.0.0.1:3000") == "http://127.0.0.1:3000"
    assert validate_loopback_base_url("http://localhost:3000/") == "http://localhost:3000"
    with pytest.raises(ValueError):
        validate_loopback_base_url("https://example.com")
    with pytest.raises(ValueError):
        validate_loopback_base_url("http://user:pass@localhost:3000")

    disposable_url = (
        "postgresql+psycopg://postgres:qa-only@127.0.0.1:15432/vitta_one"
    )
    validate_disposable_database_url(
        disposable_url,
        enabled="yes",
        database_id="vitta-one-operational-ui-qa-db",
    )
    validate_disposable_database_url(
        disposable_url.replace("/vitta_one", "/vitta_one_operational_ui_qa"),
        enabled="yes",
        database_id="vitta-one-operational-ui-qa-db",
    )
    validate_disposable_database_url(
        disposable_url.replace("/vitta_one", "/vitta_one_operational_ui_qa_2"),
        enabled="yes",
        database_id="vitta-one-operational-ui-qa-db",
    )
    validate_disposable_database_url(
        disposable_url.replace(":15432", ":15433").replace(
            "/vitta_one", "/vitta_one_operational_ui_qa_21"
        ),
        enabled="yes",
        database_id="vitta-one-operational-ui-qa-db",
    )
    with pytest.raises(RuntimeError):
        validate_disposable_database_url(
            disposable_url.replace(":15432", ":15433"),
            enabled="yes",
            database_id="vitta-one-operational-ui-qa-db",
        )
    with pytest.raises(RuntimeError):
        validate_disposable_database_url(
            disposable_url.replace(":15432", ":5432"),
            enabled="yes",
            database_id="vitta-one-operational-ui-qa-db",
        )
    with pytest.raises(RuntimeError):
        validate_disposable_database_url(
            disposable_url,
            enabled="yes",
            database_id="",
        )
    with pytest.raises(RuntimeError):
        validate_disposable_database_url(
            disposable_url.replace("/vitta_one", "/postgres"),
            enabled="yes",
            database_id="vitta-one-operational-ui-qa-db",
        )
