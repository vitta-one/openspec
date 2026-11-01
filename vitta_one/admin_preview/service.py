"""Authorization boundary for the explicit local Administrator QA preview."""

from sqlmodel import Session, select

from vitta_one.models import Patient, QueueEntry

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


def get_preview_patient_identity(
    db: Session, *, token: str, patient_id: int
) -> Patient | None:
    """Authorize a QA patient read before resolving any resource by ID."""
    require_local_admin_preview(db, token)
    if patient_id < 1:
        return None
    return db.get(Patient, patient_id)


def get_preview_patient_detail(
    db: Session, *, token: str, patient_id: int
) -> tuple[Patient | None, list[QueueEntry]]:
    """Return only this patient's identity and operational events, never clinical data."""
    patient = get_preview_patient_identity(db, token=token, patient_id=patient_id)
    if patient is None:
        return None, []
    entries = list(
        db.exec(
            select(QueueEntry)
            .where(QueueEntry.patient_id == patient_id)
            .order_by(QueueEntry.entered_at.desc())
        ).all()
    )
    return patient, entries
