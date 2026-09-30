"""Vitta-One Reflex application entry point."""

import reflex as rx

from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState
from vitta_one.models import (
    AuthSession,
    Patient,
    Professional,
    ProfessionalSpecialty,
    QueueEntry,
    Specialty,
    User,
)
from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState
from vitta_one.professional_directory.state import AdminDirectoryState
from vitta_one.ui.pages import (
    admin_page,
    doctor_page,
    finance_page,
    forbidden_page,
    login_page,
    reception_page,
    root_page,
)

# Keep persistent models imported from the application module so Reflex/Alembic
# can discover their metadata when generating migrations.
_PERSISTENT_MODELS = (
    User,
    AuthSession,
    Patient,
    QueueEntry,
    Specialty,
    Professional,
    ProfessionalSpecialty,
)

app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="teal",
        gray_color="slate",
        radius="large",
    ),
    stylesheets=["/styles.css"],
)

app.add_page(
    root_page,
    route="/",
    title="Vitta-One",
    on_load=AuthState.route_from_root,
)
app.add_page(
    login_page,
    route="/login",
    title="Entrar | Vitta-One",
    on_load=AuthState.prepare_login,
)
app.add_page(
    admin_page,
    route=Role.ADMINISTRADOR.dashboard_path,
    title="Painel administrativo | Vitta-One",
    on_load=[AuthState.load_protected, AdminDirectoryState.load],
)
app.add_page(
    reception_page,
    route=Role.RECEPCIONISTA.dashboard_path,
    title="Painel de recepção | Vitta-One",
    on_load=[AuthState.load_protected, ReceptionQueueState.load],
)
app.add_page(
    doctor_page,
    route=Role.MEDICO.dashboard_path,
    title="Painel médico | Vitta-One",
    on_load=[AuthState.load_protected, DoctorQueueState.load],
)
app.add_page(
    finance_page,
    route=Role.FINANCEIRO.dashboard_path,
    title="Painel financeiro | Vitta-One",
    on_load=AuthState.load_protected,
)
app.add_page(
    forbidden_page,
    route="/acesso-negado",
    title="Acesso não autorizado | Vitta-One",
    on_load=AuthState.prepare_forbidden,
)
