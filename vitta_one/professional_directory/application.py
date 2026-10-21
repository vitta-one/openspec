"""Administrator-only application operations for professional directory management."""

from sqlmodel import Session

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.models.professional import Professional, Specialty
from vitta_one.professional_directory.service import (
    MedicalAccountOption,
    ProfessionalItem,
    SpecialtyItem,
    create_professional,
    create_specialty,
    register_medical_professional,
    update_professional_onboarding_status,
    MedicalRegistrationResult,
    reissue_medical_temporary_password,
    list_available_medical_accounts,
    list_professionals,
    list_specialties,
    rename_specialty,
    set_professional_active,
    set_specialty_active,
    update_professional,
)


def admin_list_specialties(db: Session, *, token: str) -> list[SpecialtyItem]:
    require_role(db, token, Role.ADMINISTRADOR)
    return list_specialties(db)


def admin_list_recent_specialties(
    db: Session, *, token: str, limit: int = 3
) -> list[SpecialtyItem]:
    """Read dashboard specialties with RBAC and a server-side row limit."""
    require_role(db, token, Role.ADMINISTRADOR)
    return list_specialties(db, recent_limit=limit)


def admin_create_specialty(db: Session, *, token: str, name: str) -> Specialty:
    require_role(db, token, Role.ADMINISTRADOR)
    return create_specialty(db, name=name)


def admin_rename_specialty(
    db: Session, *, token: str, specialty_id: int, name: str
) -> Specialty:
    require_role(db, token, Role.ADMINISTRADOR)
    return rename_specialty(db, specialty_id=specialty_id, name=name)


def admin_set_specialty_active(
    db: Session, *, token: str, specialty_id: int, is_active: bool
) -> Specialty:
    require_role(db, token, Role.ADMINISTRADOR)
    return set_specialty_active(db, specialty_id=specialty_id, is_active=is_active)


def admin_list_professionals(db: Session, *, token: str) -> list[ProfessionalItem]:
    require_role(db, token, Role.ADMINISTRADOR)
    return list_professionals(db)


def admin_list_recent_professionals(
    db: Session, *, token: str, limit: int = 3
) -> list[ProfessionalItem]:
    """Read dashboard professionals with RBAC and a server-side row limit."""
    require_role(db, token, Role.ADMINISTRADOR)
    return list_professionals(db, recent_limit=limit)


def admin_create_professional(
    db: Session,
    *,
    token: str,
    name: str,
    registration_identifier: str,
    specialty_ids: list[int] | tuple[int, ...],
    user_id: int | None,
) -> Professional:
    require_role(db, token, Role.ADMINISTRADOR)
    return create_professional(
        db,
        name=name,
        registration_identifier=registration_identifier,
        specialty_ids=specialty_ids,
        user_id=user_id,
    )


def admin_update_professional(
    db: Session,
    *,
    token: str,
    professional_id: int,
    name: str,
    registration_identifier: str,
    specialty_ids: list[int] | tuple[int, ...],
    user_id: int | None,
) -> Professional:
    require_role(db, token, Role.ADMINISTRADOR)
    return update_professional(
        db,
        professional_id=professional_id,
        name=name,
        registration_identifier=registration_identifier,
        specialty_ids=specialty_ids,
        user_id=user_id,
    )


def admin_set_professional_active(
    db: Session, *, token: str, professional_id: int, is_active: bool
) -> Professional:
    require_role(db, token, Role.ADMINISTRADOR)
    return set_professional_active(
        db,
        professional_id=professional_id,
        is_active=is_active,
    )


def admin_list_available_medical_accounts(
    db: Session,
    *,
    token: str,
    professional_id: int | None = None,
) -> list[MedicalAccountOption]:
    require_role(db, token, Role.ADMINISTRADOR)
    return list_available_medical_accounts(db, professional_id=professional_id)


def admin_register_medical_professional(
    db: Session, *, token: str, name: str, email: str,
    specialty_ids: list[int] | tuple[int, ...],
    local_qa_password: str | None = None,
) -> MedicalRegistrationResult:
    require_role(db, token, Role.ADMINISTRADOR)
    return register_medical_professional(
        db, name=name, email=email, specialty_ids=specialty_ids,
        local_qa_password=local_qa_password,
    )


def admin_set_onboarding_email_status(
    db: Session, *, token: str, professional_id: int,
    status: str, message_id: str | None = None,
) -> None:
    require_role(db, token, Role.ADMINISTRADOR)
    update_professional_onboarding_status(
        db, professional_id=professional_id, status=status, message_id=message_id
    )


def admin_reissue_medical_access(
    db: Session, *, token: str, professional_id: int
) -> MedicalRegistrationResult:
    require_role(db, token, Role.ADMINISTRADOR)
    return reissue_medical_temporary_password(
        db, professional_id=professional_id
    )
