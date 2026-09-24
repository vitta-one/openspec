"""Security helpers for credentials and opaque sessions."""

import hashlib
import secrets

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_PASSWORD_HASHER = PasswordHasher(type=Type.ID)
_SESSION_TOKEN_BYTES = 48


def normalize_email(email: str) -> str:
    """Normalize an e-mail identifier before persistence or lookup."""
    return email.strip().casefold()


def is_valid_email_identifier(email: str) -> bool:
    """Validate the minimal server-side shape accepted for a login e-mail identifier."""
    normalized = normalize_email(email)
    if not normalized or len(normalized) > 320 or any(char.isspace() for char in normalized):
        return False
    if normalized.count("@") != 1:
        return False
    local_part, domain = normalized.split("@", 1)
    return bool(local_part and domain)


def hash_password(password: str) -> str:
    """Hash a password with Argon2id using argon2-cffi safe defaults."""
    if not password:
        raise ValueError("A senha não pode ser vazia.")
    return _PASSWORD_HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Verify a password without leaking the reason for authentication failure."""
    if not password_hash or not password:
        return False

    try:
        return _PASSWORD_HASHER.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def new_session_token() -> str:
    """Generate an unpredictable opaque token for the browser session identifier."""
    return secrets.token_urlsafe(_SESSION_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    """Hash a session token before storing or querying it in the database."""
    if not token:
        raise ValueError("O token de sessão não pode ser vazio.")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
