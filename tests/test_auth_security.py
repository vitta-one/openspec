"""Unit tests for pure authentication security helpers."""

from vitta_one.auth.roles import Role
from vitta_one.auth.security import (
    hash_password,
    hash_session_token,
    is_valid_email_identifier,
    new_session_token,
    normalize_email,
    verify_password,
)


def test_normalize_email_trims_and_casefolds() -> None:
    assert normalize_email("  Usuario@EXEMPLO.COM  ") == "usuario@exemplo.com"


def test_email_identifier_requires_basic_valid_shape() -> None:
    assert is_valid_email_identifier("usuario@exemplo.com") is True
    assert is_valid_email_identifier(" usuario@EXEMPLO.COM ") is True
    assert is_valid_email_identifier("sem-arroba") is False
    assert is_valid_email_identifier("@exemplo.com") is False
    assert is_valid_email_identifier("usuario@") is False
    assert is_valid_email_identifier("usuario @exemplo.com") is False
    assert is_valid_email_identifier("a@b@c.com") is False


def test_password_hash_round_trip_and_wrong_password() -> None:
    plain_text = "uma-senha-de-teste"
    password_hash = hash_password(plain_text)

    assert password_hash.startswith("$argon2id$")
    assert plain_text not in password_hash
    assert verify_password(password_hash, plain_text) is True
    assert verify_password(password_hash, "senha-incorreta") is False


def test_malformed_hash_is_rejected_without_exception() -> None:
    assert verify_password("nao-e-um-hash-argon2", "qualquer") is False


def test_session_tokens_are_unpredictable_and_only_hash_is_persistable() -> None:
    first = new_session_token()
    second = new_session_token()

    assert first != second
    assert len(hash_session_token(first)) == 64
    assert hash_session_token(first) != first


def test_role_set_is_exactly_the_domain_roles() -> None:
    assert {role.value for role in Role} == {
        "ADMINISTRADOR",
        "RECEPCIONISTA",
        "MEDICO",
        "FINANCEIRO",
    }
