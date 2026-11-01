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


# O preview de agenda tem uma projeção própria: nenhuma identidade de paciente
# ou dado clínico precisa atravessar esse limite de autorização.
from dataclasses import dataclass
from datetime import datetime

from vitta_one.appointment_scheduling.service import (
    AvailabilitySlotItem,
    ProfessionalOption,
    list_availability_slots,
)
from vitta_one.appointment_scheduling.temporal import clinic_date_range_to_utc
from vitta_one.models.appointment import Consultation
from vitta_one.models.professional import Professional
from sqlmodel import select


@dataclass(frozen=True, slots=True)
class AdminAgendaConsultation:
    id: int
    professional_id: int
    professional_name: str
    scheduled_at: datetime
    status: str


@dataclass(frozen=True, slots=True)
class AdminAgendaSnapshot:
    professionals: tuple[ProfessionalOption, ...]
    slots: tuple[AvailabilitySlotItem, ...]
    consultations: tuple[AdminAgendaConsultation, ...]


def admin_agenda_snapshot(
    db: Session,
    *,
    token: str,
    start_date: str,
    end_date: str,
    professional_id: int | None = None,
) -> AdminAgendaSnapshot:
    """Read authorized persisted schedule data in a bounded clinic-local period."""
    require_local_admin_preview(db, token)
    start_at, end_at = clinic_date_range_to_utc(start_date, end_date)

    professionals = db.exec(
        select(Professional).order_by(Professional.name, Professional.id)
    ).all()
    if professional_id is not None and not any(
        item.id == professional_id for item in professionals
    ):
        # Identificadores enviados pelo cliente nunca ampliam o escopo de consulta.
        raise ValueError("Profissional inválido.")

    slots = list_availability_slots(
        db,
        professional_id=professional_id,
        start_at=start_at,
        end_at=end_at,
    )
    statement = (
        select(
            Consultation.id,
            Consultation.professional_id,
            Professional.name,
            Consultation.scheduled_at,
            Consultation.status,
        )
        .join(Professional, Professional.id == Consultation.professional_id)
        .where(
            Consultation.scheduled_at >= start_at,
            Consultation.scheduled_at < end_at,
        )
    )
    if professional_id is not None:
        statement = statement.where(Consultation.professional_id == professional_id)
    consultations = db.exec(
        statement.order_by(Consultation.scheduled_at, Consultation.id)
    ).all()

    return AdminAgendaSnapshot(
        professionals=tuple(
            ProfessionalOption(
                id=item.id,
                name=item.name,
                registration_identifier=item.registration_identifier,
            )
            for item in professionals
            if item.id is not None
        ),
        slots=tuple(slots),
        consultations=tuple(
            AdminAgendaConsultation(
                id=consultation_id,
                professional_id=doctor_id,
                professional_name=doctor_name,
                scheduled_at=scheduled_at,
                status=status,
            )
            for consultation_id, doctor_id, doctor_name, scheduled_at, status in consultations
        ),
    )
