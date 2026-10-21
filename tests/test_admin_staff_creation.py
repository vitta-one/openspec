"""Role restrictions and duplicate controls for receptionist accounts."""
from datetime import timedelta
import pytest
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from vitta_one.models.auth import User, AuthSession
from vitta_one.auth.staff_service import create_receptionist
from vitta_one.auth.service import create_session
from vitta_one.auth.security import hash_password, verify_password
from vitta_one.auth.roles import Role

@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine, tables=[User.__table__, AuthSession.__table__])
    with Session(engine) as s:
        yield s
    engine.dispose()

def token(db, role):
    user = User(email=f"{role.lower()}@example.invalid",
                password_hash=hash_password("testing_password_123"), role=role)
    db.add(user); db.commit(); db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))

def test_only_admin_can_create_receptionist(db):
    admin = token(db, Role.ADMINISTRADOR.value)
    reception = token(db, Role.RECEPCIONISTA.value)
    with pytest.raises(PermissionError):
        create_receptionist(db, token=reception, email="other@example.invalid", password="testing_password_123")
    user = create_receptionist(db, token=admin, email="  ReCepCAO@example.invalid ",
                              password="testing_password_123")
    assert user.email == "recepcao@example.invalid"
    assert verify_password(user.password_hash, "testing_password_123")
    with pytest.raises(ValueError, match="já está cadastrado"):
        create_receptionist(db, token=admin, email=user.email, password="testing_password_123")
    with pytest.raises(ValueError, match="12"):
        create_receptionist(db, token=admin, email="new@example.invalid", password="short")
