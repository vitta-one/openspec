"""Server-authorized creation of receptionist identities."""
from sqlmodel import Session, select
from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password, is_valid_email_identifier, normalize_email
from vitta_one.models.auth import User

def create_receptionist(db: Session, *, token: str, email: str, password: str) -> User:
    require_role(db, token, Role.ADMINISTRADOR)
    address = normalize_email(email)
    if not is_valid_email_identifier(address):
        raise ValueError("E-mail inválido.")
    if not 12 <= len(password) <= 128:
        raise ValueError("Use uma senha de 12 a 128 caracteres.")
    if db.exec(select(User).where(User.email == address)).first() is not None:
        raise ValueError("Esse e-mail já está cadastrado.")
    user = User(email=address, password_hash=hash_password(password), role=Role.RECEPCIONISTA.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def list_receptionists(db: Session, *, token: str) -> list[str]:
    require_role(db, token, Role.ADMINISTRADOR)
    return list(db.exec(select(User.email).where(User.role == Role.RECEPCIONISTA.value).order_by(User.email)).all())
