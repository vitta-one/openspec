"""Regression tests for login field errors and preserved authentication semantics."""

import pytest

from vitta_one.auth.state import _login_field_errors


@pytest.mark.parametrize(
    ("email", "password", "expected"),
    [
        ("", "", ("Informe seu e-mail.", "Informe sua senha.")),
        ("   ", "segredo", ("Informe seu e-mail.", "")),
        ("user@exemplo.com", "", ("", "Informe sua senha.")),
        ("email-invalido", "segredo", ("Informe um e-mail válido, como nome@dominio.com.", "")),
        ("a@b", "segredo", ("Informe um e-mail válido, como nome@dominio.com.", "")),
        ("user@exemplo.com", "segredo", ("", "")),
        (" USER@EXEMPLO.COM ", "segredo", ("", "")),
    ],
)
def test_login_reports_only_relevant_field_errors(email, password, expected):
    assert _login_field_errors(email, password) == expected
