"""Business services for the professional and specialty directory."""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import secrets
from uuid import uuid4

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.auth.roles import Role
from vitta_one.auth.security import (
    hash_password, normalize_email, is_valid_email_identifier,
)
from vitta_one.models.auth import User
from vitta_one.models.professional import (
    Professional,
    ProfessionalSpecialty,
    Specialty,
)


class DirectoryValidationError(ValueError):
    """Raised when administrator input is invalid."""


class DirectoryConflictError(RuntimeError):
    """Raised when a unique business key conflicts with an existing record."""


class DirectoryNotFoundError(LookupError):
    """Raised when a requested directory entity does not exist."""


@dataclass(frozen=True, slots=True)
class SpecialtyItem:
    id: int
    name: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class MedicalAccountOption:
    id: int
    email: str


@dataclass(frozen=True, slots=True)
class ProfessionalItem:
    id: int
    name: str
    registration_identifier: str
    is_active: bool
    user_id: int | None
    user_email: str | None
    specialties: tuple[SpecialtyItem, ...]
    onboarding_email_status: str = "NOT_REQUIRED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_display_name(value: str) -> str:
    """Collapse whitespace for human-facing names without changing capitalization."""
    return " ".join(str(value or "").strip().split())


def normalize_specialty_key(value: str) -> str:
    """Return the stable case-insensitive uniqueness key for specialty names."""
    return normalize_display_name(value).casefold()


def normalize_registration_identifier(value: str) -> str:
    """Normalize a generic professional identifier without assuming a council."""
    return " ".join(str(value or "").strip().split()).upper()


def _validate_specialty_name(value: str) -> tuple[str, str]:
    display = normalize_display_name(value)
    if not display:
        raise DirectoryValidationError("Informe o nome da especialidade.")
    if len(display) > 120:
        raise DirectoryValidationError("O nome da especialidade excede o limite permitido.")
    return display, normalize_specialty_key(display)


def _validate_professional_name(value: str) -> str:
    display = normalize_display_name(value)
    if not display:
        raise DirectoryValidationError("Informe o nome do profissional.")
    if len(display) > 160:
        raise DirectoryValidationError("O nome do profissional excede o limite permitido.")
    return display


def _validate_registration_identifier(value: str) -> str:
    normalized = normalize_registration_identifier(value)
    if not normalized:
        raise DirectoryValidationError("Informe o identificador profissional.")
    if len(normalized) > 80:
        raise DirectoryValidationError(
            "O identificador profissional excede o limite permitido."
        )
    return normalized


def create_specialty(db: Session, *, name: str) -> Specialty:
    display, normalized = _validate_specialty_name(name)

    if db.exec(
        select(Specialty).where(Specialty.normalized_name == normalized)
    ).first():
        raise DirectoryConflictError("Já existe uma especialidade com esse nome.")

    specialty = Specialty(name=display, normalized_name=normalized, is_active=True)
    db.add(specialty)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DirectoryConflictError("Já existe uma especialidade com esse nome.") from exc
    db.refresh(specialty)
    return specialty


def list_specialties(
    db: Session, *, recent_limit: int | None = None
) -> list[SpecialtyItem]:
    """List all specialties or the N most recently created ones for a dashboard."""
    statement = select(Specialty)
    if recent_limit is not None:
        if not 1 <= recent_limit <= 100:
            raise ValueError("Limite de resultados inválido.")
        statement = statement.order_by(
            Specialty.created_at.desc(), Specialty.id.desc()
        ).limit(recent_limit)
    else:
        statement = statement.order_by(Specialty.name, Specialty.id)
    rows = db.exec(statement).all()
    return [
        SpecialtyItem(id=row.id, name=row.name, is_active=row.is_active)
        for row in rows
        if row.id is not None
    ]


def rename_specialty(db: Session, *, specialty_id: int, name: str) -> Specialty:
    specialty = db.get(Specialty, specialty_id)
    if specialty is None:
        raise DirectoryNotFoundError("A especialidade não está disponível.")

    display, normalized = _validate_specialty_name(name)
    duplicate = db.exec(
        select(Specialty).where(
            Specialty.normalized_name == normalized,
            Specialty.id != specialty_id,
        )
    ).first()
    if duplicate is not None:
        raise DirectoryConflictError("Já existe uma especialidade com esse nome.")

    specialty.name = display
    specialty.normalized_name = normalized
    specialty.updated_at = utc_now()
    db.add(specialty)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DirectoryConflictError("Já existe uma especialidade com esse nome.") from exc
    db.refresh(specialty)
    return specialty


def set_specialty_active(
    db: Session, *, specialty_id: int, is_active: bool
) -> Specialty:
    specialty = db.get(Specialty, specialty_id)
    if specialty is None:
        raise DirectoryNotFoundError("A especialidade não está disponível.")
    specialty.is_active = bool(is_active)
    specialty.updated_at = utc_now()
    db.add(specialty)
    db.commit()
    db.refresh(specialty)
    return specialty


def _association_ids(db: Session, professional_id: int) -> set[int]:
    rows = db.exec(
        select(ProfessionalSpecialty.specialty_id).where(
            ProfessionalSpecialty.professional_id == professional_id
        )
    ).all()
    return {int(value) for value in rows}


def _validate_specialty_ids(
    db: Session,
    specialty_ids: list[int] | tuple[int, ...],
    *,
    existing_ids: set[int] | None = None,
) -> list[int]:
    unique_ids = list(dict.fromkeys(int(value) for value in specialty_ids))
    if not unique_ids:
        raise DirectoryValidationError(
            "Selecione ao menos uma especialidade para o profissional."
        )

    rows = db.exec(
        select(Specialty).where(Specialty.id.in_(unique_ids))
    ).all()
    by_id = {row.id: row for row in rows if row.id is not None}
    if len(by_id) != len(unique_ids):
        raise DirectoryValidationError("Uma das especialidades selecionadas não existe.")

    historical = existing_ids or set()
    inactive_new = [
        specialty_id
        for specialty_id in unique_ids
        if not by_id[specialty_id].is_active and specialty_id not in historical
    ]
    if inactive_new:
        raise DirectoryValidationError(
            "Especialidades inativas não podem ser adicionadas a um profissional."
        )

    return unique_ids


def _validate_medical_user(
    db: Session,
    *,
    user_id: int | None,
    professional_id: int | None = None,
) -> User | None:
    if user_id is None:
        return None

    user = db.get(User, user_id)
    if user is None or user.role != Role.MEDICO.value:
        raise DirectoryValidationError(
            "A conta selecionada precisa existir e possuir a role Médico."
        )

    statement = select(Professional).where(Professional.user_id == user_id)
    if professional_id is not None:
        statement = statement.where(Professional.id != professional_id)
    if db.exec(statement).first() is not None:
        raise DirectoryConflictError(
            "Esta conta Médica já está vinculada a outro profissional."
        )
    return user


def _validate_registration_unique(
    db: Session,
    registration_identifier: str,
    *,
    professional_id: int | None = None,
) -> None:
    statement = select(Professional).where(
        Professional.registration_identifier == registration_identifier
    )
    if professional_id is not None:
        statement = statement.where(Professional.id != professional_id)
    if db.exec(statement).first() is not None:
        raise DirectoryConflictError(
            "Já existe um profissional com esse identificador."
        )


def create_professional(
    db: Session,
    *,
    name: str,
    registration_identifier: str,
    specialty_ids: list[int] | tuple[int, ...],
    user_id: int | None = None,
) -> Professional:
    display_name = _validate_professional_name(name)
    normalized_identifier = _validate_registration_identifier(registration_identifier)
    _validate_registration_unique(db, normalized_identifier)
    valid_specialties = _validate_specialty_ids(db, specialty_ids)
    _validate_medical_user(db, user_id=user_id)

    professional = Professional(
        name=display_name,
        registration_identifier=normalized_identifier,
        user_id=user_id,
        is_active=True,
    )
    db.add(professional)
    try:
        db.flush()
        if professional.id is None:
            raise RuntimeError("Profissional criado sem identificador.")
        for specialty_id in valid_specialties:
            db.add(
                ProfessionalSpecialty(
                    professional_id=professional.id,
                    specialty_id=specialty_id,
                )
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DirectoryConflictError(
            "Não foi possível salvar o profissional por conflito de dados únicos."
        ) from exc
    db.refresh(professional)
    return professional


def update_professional(
    db: Session,
    *,
    professional_id: int,
    name: str,
    registration_identifier: str,
    specialty_ids: list[int] | tuple[int, ...],
    user_id: int | None = None,
) -> Professional:
    professional = db.get(Professional, professional_id)
    if professional is None:
        raise DirectoryNotFoundError("O profissional não está disponível.")

    display_name = _validate_professional_name(name)
    normalized_identifier = _validate_registration_identifier(registration_identifier)
    _validate_registration_unique(
        db,
        normalized_identifier,
        professional_id=professional_id,
    )
    existing_specialties = _association_ids(db, professional_id)
    valid_specialties = _validate_specialty_ids(
        db,
        specialty_ids,
        existing_ids=existing_specialties,
    )
    _validate_medical_user(
        db,
        user_id=user_id,
        professional_id=professional_id,
    )

    professional.name = display_name
    professional.registration_identifier = normalized_identifier
    professional.user_id = user_id
    professional.updated_at = utc_now()

    db.exec(
        delete(ProfessionalSpecialty).where(
            ProfessionalSpecialty.professional_id == professional_id
        )
    )
    for specialty_id in valid_specialties:
        db.add(
            ProfessionalSpecialty(
                professional_id=professional_id,
                specialty_id=specialty_id,
            )
        )
    db.add(professional)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DirectoryConflictError(
            "Não foi possível atualizar o profissional por conflito de dados únicos."
        ) from exc
    db.refresh(professional)
    return professional


def set_professional_active(
    db: Session, *, professional_id: int, is_active: bool
) -> Professional:
    professional = db.get(Professional, professional_id)
    if professional is None:
        raise DirectoryNotFoundError("O profissional não está disponível.")
    professional.is_active = bool(is_active)
    professional.updated_at = utc_now()
    db.add(professional)
    db.commit()
    db.refresh(professional)
    return professional


def list_professionals(
    db: Session, *, recent_limit: int | None = None
) -> list[ProfessionalItem]:
    """List professionals in directory order, or newest first with an SQL limit."""
    statement = select(Professional)
    if recent_limit is not None:
        if not 1 <= recent_limit <= 100:
            raise ValueError("Limite de resultados inválido.")
        statement = statement.order_by(
            Professional.created_at.desc(), Professional.id.desc()
        ).limit(recent_limit)
    else:
        statement = statement.order_by(Professional.name, Professional.id)
    professionals = db.exec(statement).all()
    output: list[ProfessionalItem] = []

    for professional in professionals:
        if professional.id is None:
            continue
        associations = db.exec(
            select(ProfessionalSpecialty).where(
                ProfessionalSpecialty.professional_id == professional.id
            )
        ).all()
        specialty_ids = [row.specialty_id for row in associations]
        specialties: list[SpecialtyItem] = []
        if specialty_ids:
            rows = db.exec(
                select(Specialty)
                .where(Specialty.id.in_(specialty_ids))
                .order_by(Specialty.name, Specialty.id)
            ).all()
            specialties = [
                SpecialtyItem(id=row.id, name=row.name, is_active=row.is_active)
                for row in rows
                if row.id is not None
            ]

        user_email: str | None = None
        if professional.user_id is not None:
            user = db.get(User, professional.user_id)
            if user is not None:
                user_email = user.email

        output.append(
            ProfessionalItem(
                id=professional.id,
                name=professional.name,
                registration_identifier=professional.registration_identifier,
                is_active=professional.is_active,
                user_id=professional.user_id,
                user_email=user_email,
                specialties=tuple(specialties),
                onboarding_email_status=professional.onboarding_email_status,
            )
        )

    return output


def list_available_medical_accounts(
    db: Session, *, professional_id: int | None = None
) -> list[MedicalAccountOption]:
    used = {
        row.user_id
        for row in db.exec(
            select(Professional).where(Professional.user_id.is_not(None))
        ).all()
        if row.user_id is not None and row.id != professional_id
    }
    users = db.exec(
        select(User)
        .where(User.role == Role.MEDICO.value)
        .order_by(User.email, User.id)
    ).all()
    return [
        MedicalAccountOption(id=user.id, email=user.email)
        for user in users
        if user.id is not None and user.id not in used
    ]


@dataclass(frozen=True, slots=True)
class MedicalRegistrationResult:
    """Temporary secret MUST stay in the server event stack, never Reflex State."""

    professional_id: int
    user_id: int
    email: str
    name: str
    temporary_password: str | None


def register_medical_professional(
    db: Session,
    *,
    name: str,
    email: str,
    specialty_ids: list[int] | tuple[int, ...],
) -> MedicalRegistrationResult:
    """Atomically create a doctor identity and professional without changing legacy users."""
    display_name = _validate_professional_name(name)
    normalized_email = normalize_email(email)
    if not is_valid_email_identifier(normalized_email):
        raise DirectoryValidationError("Informe um e-mail profissional válido.")
    valid_specialties = _validate_specialty_ids(db, specialty_ids)

    user = db.exec(select(User).where(User.email == normalized_email)).first()
    if user is not None:
        if user.role != Role.MEDICO.value:
            raise DirectoryConflictError("Este e-mail já pertence a outro tipo de conta.")
        if db.exec(select(Professional).where(Professional.user_id == user.id)).first():
            raise DirectoryConflictError("Este e-mail já está vinculado a um profissional.")
    temporary_password: str | None = None
    if user is None:
        temporary_password = secrets.token_urlsafe(32)
        user = User(
            email=normalized_email,
            role=Role.MEDICO.value,
            password_hash=hash_password(temporary_password),
            must_change_password=True,
            temporary_password_expires_at=utc_now() + timedelta(hours=24),
        )
        db.add(user)

    # A generated local key is not a professional council/CRM identifier.
    registration_identifier = "INT-" + uuid4().hex.upper()
    try:
        db.flush()
        if user.id is None:
            raise RuntimeError("Identidade médica não recebeu identificador.")
        professional = Professional(
            name=display_name,
            registration_identifier=registration_identifier,
            user_id=user.id,
            is_active=True,
            onboarding_email_status="PENDING" if temporary_password else "NOT_REQUIRED",
        )
        db.add(professional)
        db.flush()
        if professional.id is None:
            raise RuntimeError("Profissional não recebeu identificador.")
        for specialty_id in valid_specialties:
            db.add(
                ProfessionalSpecialty(
                    professional_id=professional.id,
                    specialty_id=specialty_id,
                )
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DirectoryConflictError(
            "Este e-mail ou profissional já foi cadastrado. Confira os dados."
        ) from exc
    db.refresh(professional)
    return MedicalRegistrationResult(
        professional_id=professional.id,
        user_id=user.id,
        email=normalized_email,
        name=display_name,
        temporary_password=temporary_password,
    )


def update_professional_onboarding_status(
    db: Session, *, professional_id: int, status: str, message_id: str | None = None
) -> None:
    """Persist provider request status only, never any credential or message body."""
    allowed = {"ACCEPTED", "FAILED", "UNKNOWN", "NOT_CONFIGURED"}
    if status not in allowed:
        raise DirectoryValidationError("Situação de e-mail inválida.")
    professional = db.get(Professional, professional_id)
    if professional is None:
        raise DirectoryNotFoundError("Profissional não localizado.")
    if professional.onboarding_email_status not in {
        "PENDING", "FAILED", "UNKNOWN", "NOT_CONFIGURED"
    }:
        raise DirectoryConflictError("Nenhum onboarding pendente para este profissional.")
    professional.onboarding_email_status = status
    professional.onboarding_email_message_id = (
        message_id[:128] if status == "ACCEPTED" and message_id else None
    )
    db.add(professional)
    db.commit()
