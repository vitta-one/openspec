"""Authorization boundary for the explicit local Administrator QA preview."""

from sqlmodel import Session

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.auth.service import AuthenticatedUser
from vitta_one.auth.settings import local_admin_preview_enabled


class LocalAdminPreviewDisabledError(PermissionError):
    """Raised when a local-only preview route is disabled by configuration."""


def require_local_admin_preview(db: Session, token: str) -> AuthenticatedUser:
    """Require explicit local-preview configuration and an Administrator session."""
    if not local_admin_preview_enabled():
        raise LocalAdminPreviewDisabledError(
            "A visualização local do Administrador está desabilitada."
        )
    return require_role(db, token, Role.ADMINISTRADOR)
