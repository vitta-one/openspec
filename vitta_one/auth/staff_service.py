"""Server-authorized creation of receptionist identities."""
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password, is_valid_email_identifier, normalize_email
from vitta_one.models.auth import User
from vitta_one.models.professional import Professional, ProfessionalSpecialty, Specialty

def create_receptionist(db: Session, *, token: str, email: str, password: str, name: str | None = None) -> User:
    require_role(db, token, Role.ADMINISTRADOR)
    display_name = " ".join((name or "").split())
    if not 2 <= len(display_name) <= 160:
        raise ValueError("Informe um nome de 2 a 160 caracteres.")
    address = normalize_email(email)
    if not is_valid_email_identifier(address):
        raise ValueError("E-mail inválido.")
    if not 12 <= len(password) <= 128:
        raise ValueError("Use uma senha de 12 a 128 caracteres.")
    if db.exec(select(User).where(User.email == address)).first() is not None:
        raise ValueError("Esse e-mail já está cadastrado.")
    user = User(email=address, display_name=display_name, password_hash=hash_password(password), role=Role.RECEPCIONISTA.value)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Esse e-mail já está cadastrado.") from exc
    db.refresh(user)
    return user

def list_receptionists(db: Session, *, token: str) -> list[str]:
    require_role(db, token, Role.ADMINISTRADOR)
    return list(db.exec(select(User.email).where(User.role == Role.RECEPCIONISTA.value).order_by(User.email)).all())


def list_employee_directory(db: Session, *, token: str) -> list[dict]:
    """A read-only, admin-authorized list of staff identities (never patient users)."""
    require_role(db, token, Role.ADMINISTRADOR)
    users = db.exec(
        select(User)
        .where(User.role.in_((Role.MEDICO.value, Role.RECEPCIONISTA.value)))
        .order_by(User.created_at.desc(), User.id.desc())
    ).all()
    return [
        {"id": user.id, "email": user.email, "name": user.display_name or "Nome não informado", "role": user.role,
         "role_label": ("Médico" if user.role == Role.MEDICO.value else "Recepcionista"),
         "href": f"/admin/funcionarios/{user.id}"}
        for user in users
    ]


def get_employee_detail(db: Session, *, token: str, employee_id: int) -> dict | None:
    """Return authorized staff identity and only its persisted professional linkage."""
    require_role(db, token, Role.ADMINISTRADOR)
    user = db.get(User, employee_id)
    if user is None or user.role not in (Role.MEDICO.value, Role.RECEPCIONISTA.value):
        return None

    professional = None
    specialty_names: list[str] = []
    if user.role == Role.MEDICO.value:
        professional = db.exec(
            select(Professional).where(Professional.user_id == user.id)
        ).first()
        if professional is not None:
            specialty_names = list(db.exec(
                select(Specialty.name)
                .join(
                    ProfessionalSpecialty,
                    ProfessionalSpecialty.specialty_id == Specialty.id,
                )
                .where(ProfessionalSpecialty.professional_id == professional.id)
                .order_by(Specialty.name)
            ).all())

    # Older accounts may lack display_name; never present their e-mail as a person's name.
    name = (user.display_name or "").strip()
    if not name and professional is not None:
        name = professional.name.strip()

    return {
        "id": user.id,
        "email": user.email,
        "name": name or "Nome não informado",
        "has_name": bool(name),
        "role": user.role,
        "role_label": "Médico" if user.role == Role.MEDICO.value else "Recepcionista",
        "href": f"/admin/funcionarios/{user.id}",
        "professional_identifier": (
            professional.registration_identifier if professional is not None else ""
        ),
        "professional_status": (
            ("Ativo" if professional.is_active else "Inativo")
            if professional is not None else ""
        ),
        "specialties": ", ".join(specialty_names),
    }


def filter_employee_directory(
    rows: list[dict], *, search: str = "", role: str = "todos"
) -> list[dict]:
    """Filter an already authorized employee directory without mutating records."""
    term = search.strip().casefold()
    return [
        row for row in rows
        if (role == "todos" or row["role"] == role)
        and (
            not term
            or any(
                term in str(row[field]).casefold()
                for field in ("name", "email", "role_label")
            )
        )
    ]
