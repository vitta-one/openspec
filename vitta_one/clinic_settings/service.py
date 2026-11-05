"""Authorization, validation, concurrency, and persistence for clinic settings."""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.models.clinic_settings import ClinicConfiguration, ClinicConfigurationChange
from vitta_one.patient_portal.settings import ClinicLocation, clinic_location


class ClinicSettingsValidationError(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field


class ClinicSettingsConflictError(ValueError):
    """The administrator edited an out-of-date configuration revision."""


def _clean(value: str, *, field: str, limit: int, label: str) -> str:
    if not isinstance(value, str):
        raise ClinicSettingsValidationError(field, f"Informe {label}.")
    if any(ord(character) < 32 and character not in "\r\n\t" for character in value):
        raise ClinicSettingsValidationError(field, f"{label.capitalize()} contém caracteres inválidos.")
    clean = " ".join(value.split())
    if not clean:
        raise ClinicSettingsValidationError(field, f"Informe {label}.")
    if len(clean) > limit:
        raise ClinicSettingsValidationError(field, f"{label.capitalize()} deve ter no máximo {limit} caracteres.")
    return clean


def get_clinic_location(db: Session) -> ClinicLocation:
    """Prefer persisted values; use legacy environment only before first save."""
    configuration = db.get(ClinicConfiguration, 1)
    if configuration is None:
        return clinic_location()
    return ClinicLocation(
        name=configuration.name,
        address=configuration.address,
        configured=True,
        persisted=True,
        revision=configuration.revision,
    )


def save_clinic_location(
    db: Session, *, token: str, name: str, address: str, expected_revision: int
) -> ClinicLocation:
    """Update the singleton and audit row atomically, with admin and revision checks."""
    identity = require_role(db, token, Role.ADMINISTRADOR)
    name = _clean(name, field="name", limit=160, label="o nome da clínica")
    address = _clean(address, field="address", limit=500, label="o endereço da clínica")
    if not isinstance(expected_revision, int) or expected_revision < 0:
        raise ClinicSettingsConflictError("Versão de configuração inválida.")

    configuration = db.exec(
        select(ClinicConfiguration)
        .where(ClinicConfiguration.id == 1)
        .with_for_update()
    ).first()
    current_revision = configuration.revision if configuration else 0
    if current_revision != expected_revision:
        raise ClinicSettingsConflictError("A configuração foi alterada em outra sessão.")

    if configuration is not None and configuration.name == name and configuration.address == address:
        return get_clinic_location(db)

    old_name = configuration.name if configuration else None
    old_address = configuration.address if configuration else None
    now = datetime.now(timezone.utc)
    if configuration is None:
        configuration = ClinicConfiguration(
            id=1, name=name, address=address, revision=1,
            updated_at=now, updated_by_user_id=identity.id,
        )
    else:
        configuration.name = name
        configuration.address = address
        configuration.revision += 1
        configuration.updated_at = now
        configuration.updated_by_user_id = identity.id
    db.add(configuration)
    db.add(
        ClinicConfigurationChange(
            previous_name=old_name, previous_address=old_address,
            name=name, address=address, actor_user_id=identity.id, occurred_at=now,
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ClinicSettingsConflictError("A configuração mudou durante o salvamento.") from exc
    except Exception:
        db.rollback()
        raise
    return ClinicLocation(
        name=name, address=address, configured=True,
        persisted=True, revision=configuration.revision,
    )
