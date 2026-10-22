"""Enable demo logins for existing medical/patient records in one dedicated local QA DB.

Never use this in production. No endpoint is exposed.
"""
import argparse
from getpass import getpass
from os import environ
from sqlalchemy.engine import make_url
from sqlmodel import Session, create_engine, select
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password, normalize_email, is_valid_email_identifier
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional

def main() -> int:
    parser = argparse.ArgumentParser(description="Ativar logins fictícios locais no Vitta-One")
    parser.add_argument("--role", choices=("medico", "paciente"), required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--cpf", help="CPF já cadastrado na Recepção, somente para paciente")
    args = parser.parse_args()
    url = make_url(environ.get("DATABASE_URL", ""))
    if (url.drivername != "postgresql+psycopg"
        or url.host not in ("localhost", "127.0.0.1")
        or url.port != 5433 or url.database != "vitta_one_qa"
        or url.username != "vittaqa"
        or environ.get("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "").lower() != "true"):
        raise SystemExit("Recusado: somente QA local vittaqa:5433/vitta_one_qa.")
    email = normalize_email(args.email)
    if not is_valid_email_identifier(email):
        raise SystemExit("E-mail inválido.")
    cpf = "".join(c for c in (args.cpf or "") if c.isdigit())
    if args.role == "paciente" and len(cpf) != 11:
        raise SystemExit("Informe --cpf de paciente cadastrado pela Recepção.")
    if args.role == "medico" and args.cpf:
        raise SystemExit("--cpf é exclusivo do paciente.")
    password = getpass("Senha de QA (12 a 128 caracteres): ")
    if not 12 <= len(password) <= 128:
        raise SystemExit("Senha de QA deve ter de 12 a 128 caracteres.")
    if password != getpass("Repita a senha de QA: "):
        raise SystemExit("As senhas não coincidem.")
    with Session(create_engine(environ["DATABASE_URL"])) as db:
        user = db.exec(select(User).where(User.email == email)).first()
        if args.role == "medico":
            if user is None or user.role != Role.MEDICO.value:
                raise SystemExit("Crie primeiro o Médico no Admin com esse e-mail.")
            professional = db.exec(select(Professional).where(Professional.user_id == user.id)).first()
            if professional is None:
                raise SystemExit("Médico sem vínculo profissional.")
            if not user.must_change_password:
                raise SystemExit("Conta médica já ativada; senha preservada.")
            user.password_hash = hash_password(password)
            user.must_change_password = False
            user.temporary_password_expires_at = None
            db.add(user)
        else:
            patient = db.exec(select(Patient).where(Patient.cpf == cpf).with_for_update()).first()
            if patient is None:
                raise SystemExit("Cadastre o paciente pela Recepção antes.")
            if patient.user_id is not None:
                raise SystemExit("Paciente já possui login; nenhum dado alterado.")
            if user is not None:
                raise SystemExit("E-mail já utilizado.")
            user = User(email=email, role=Role.PACIENTE.value,
                        password_hash=hash_password(password))
            db.add(user)
            db.flush()
            patient.user_id = user.id
            db.add(patient)
        db.commit()
    print("Conta habilitada no QA local; faça login em /login.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
