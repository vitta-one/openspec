"""Reusable server-side authorization checks for protected Vitta-One operations."""

from sqlmodel import Session

from vitta_one.auth.roles import Role
from vitta_one.auth.service import AuthenticatedUser, resolve_session


class AuthenticationRequiredError(PermissionError):
    """Raised when a protected server operation has no valid authenticated session."""


class RoleForbiddenError(PermissionError):
    """Raised when an authenticated identity does not hold the required role."""

    def __init__(self, identity: AuthenticatedUser, required_role: Role) -> None:
        super().__init__("A identidade autenticada não possui a role exigida.")
        self.identity = identity
        self.required_role = required_role


class PasswordChangeRequiredError(PermissionError):
    """Identity may only reach the initial password rotation surface."""


def require_authenticated(db: Session, token: str) -> AuthenticatedUser:
    """Resolve an authenticated identity or reject the protected server operation."""
    identity = resolve_session(db, token)
    if identity is None:
        raise AuthenticationRequiredError("Sessão autenticada válida obrigatória.")
    return identity


def require_role(db: Session, token: str, required_role: Role) -> AuthenticatedUser:
    """Require both a valid session and the exact domain role for an operation."""
    identity = require_authenticated(db, token)
    if identity.role is not required_role:
        raise RoleForbiddenError(identity, required_role)
    if identity.must_change_password:
        raise PasswordChangeRequiredError("Troca de senha inicial obrigatória.")
    return identity
