"""Vitta-One public, protected, and local QA page components."""

import reflex as rx

from vitta_one.appointment_scheduling.state import AdminAvailabilityState, ReceptionAgendaState
from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState
from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState
from vitta_one.professional_directory.state import AdminDirectoryState
from vitta_one.ui.admin_directory_components import admin_directory_workspace
from vitta_one.ui.appointment_components import admin_availability_panel, reception_agenda_panel
from vitta_one.ui.admin_preview_components import (
    agenda_preview,
    clinical_preview,
    finance_preview,
    patients_preview,
    reception_preview,
)
from vitta_one.ui.components import (
    admin_preview_workspace,
    brand_logo,
    dashboard_shell,
    feedback_region,
    loading_surface,
    login_form,
    page_header,
    protected_workspace,
)
from vitta_one.ui.prescription_components import prescription_print_page
from vitta_one.ui.queue_components import (
    active_queue_panel,
    doctor_active_panel,
    doctor_waiting_summary,
    enqueue_panel,
    patient_identity_panel,
    reassess_panel,
    withdraw_panel,
)


def root_page() -> rx.Component:
    """Render only a neutral routing surface while the session is resolved."""
    return loading_surface("Abrindo o Vitta-One…")


def login_page() -> rx.Component:
    """Render the premium internal authentication entry point."""
    content = rx.box(
        rx.box(
            rx.box(
                brand_logo(width="10rem"),
                rx.hstack(
                    rx.box(class_name="vitta-online-dot", aria_hidden="true"),
                    rx.text("Ambiente interno", font_weight="750", font_size="0.74rem"),
                    spacing="2",
                    align="center",
                    color="var(--vitta-primary)",
                    margin_top="1.25rem",
                ),
            ),
            rx.box(
                rx.text(
                    "ACESSO SEGURO",
                    class_name="vitta-login-kicker",
                ),
                rx.heading(
                    "Bem-vindo de volta.",
                    font_size=rx.breakpoints(initial="2rem", sm="2.45rem"),
                    line_height="1.08",
                    letter_spacing="-0.045em",
                    font_family="var(--vitta-font-display)",
                    margin_top="1rem",
                    class_name="vitta-login-title",
                ),
                rx.text(
                    "Entre com suas credenciais para acessar o ambiente operacional da clínica.",
                    color="var(--vitta-text-muted)",
                    line_height="1.65",
                    margin_top="0.75rem",
                    max_width="42ch",
                    class_name="vitta-login-lead",
                ),
                rx.box(login_form(), margin_top="1.75rem"),
                class_name="vitta-login-form-wrap",
            ),
            rx.hstack(
                rx.icon("shield_check", size=15),
                rx.text(
                    "Sessões e permissões são validadas no servidor.",
                    font_size="0.74rem",
                    color="var(--vitta-text-subtle)",
                ),
                spacing="2",
                align="center",
            ),
            class_name="vitta-login-form-pane",
        ),
        rx.box(
            rx.box(
                rx.box(
                    rx.icon("activity", size=42),
                    class_name="vitta-login-emblem-icon",
                ),
                rx.box(
                    width="0.65rem",
                    height="0.65rem",
                    border_radius="999px",
                    background="#ffffff",
                    opacity="0.95",
                    position="absolute",
                    right="18%",
                    top="18%",
                ),
                class_name="vitta-login-emblem",
                aria_hidden="true",
            ),
            rx.box(
                rx.text(
                    "CLÍNICA EM FOCO",
                    font_size="0.72rem",
                    font_weight="800",
                    letter_spacing="0.1em",
                    color="rgba(255,255,255,0.72)",
                ),
                rx.heading(
                    "Uma estação clínica para trabalhar com clareza.",
                    font_size=rx.breakpoints(initial="2rem", lg="3.15rem"),
                    line_height="1.04",
                    letter_spacing="-0.045em",
                    color="#ffffff",
                    font_family="var(--vitta-font-display)",
                    max_width="12ch",
                    margin_top="0.7rem",
                ),
                rx.text(
                    "Pacientes, equipe e operação organizados em uma experiência única, precisa e rastreável.",
                    color="rgba(255,255,255,0.78)",
                    line_height="1.65",
                    max_width="48ch",
                    margin_top="1rem",
                ),
                rx.flex(
                    rx.hstack(
                        rx.icon("users", size=16),
                        rx.text("Recepção", font_size="0.8rem", font_weight="700"),
                        spacing="2",
                        align="center",
                        class_name="vitta-login-feature",
                    ),
                    rx.hstack(
                        rx.icon("stethoscope", size=16),
                        rx.text("Equipe clínica", font_size="0.8rem", font_weight="700"),
                        spacing="2",
                        align="center",
                        class_name="vitta-login-feature",
                    ),
                    rx.hstack(
                        rx.icon("settings", size=16),
                        rx.text("Administração", font_size="0.8rem", font_weight="700"),
                        spacing="2",
                        align="center",
                        class_name="vitta-login-feature",
                    ),
                    gap="0.5rem",
                    flex_wrap="wrap",
                    margin_top="1.35rem",
                ),
                class_name="vitta-login-caption",
            ),
            class_name="vitta-login-visual",
        ),
        class_name="vitta-login-shell",
    )

    return rx.cond(
        AuthState.auth_checked & (AuthState.current_role == ""),
        content,
        loading_surface(),
    )


def admin_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        admin_directory_workspace(),
        admin_availability_panel(),
        active="administracao",
    )


def reception_page() -> rx.Component:
    return protected_workspace(
        Role.RECEPCIONISTA,
        page_header(
            "Operação",
            "Recepção, agenda e fila",
            "Agende Consultas, localize pacientes e acompanhe a fila ativa sem misturar os dois fluxos.",
        ),
        reception_agenda_panel(),
        feedback_region(
            ReceptionQueueState.error_message,
            ReceptionQueueState.success_message,
        ),
        rx.flex(
            patient_identity_panel(),
            enqueue_panel(),
            direction=rx.breakpoints(initial="column", xl="row"),
            gap="1rem",
            align="start",
            width="100%",
        ),
        active_queue_panel(),
        reassess_panel(),
        withdraw_panel(),
        active="recepcao",
    )


def doctor_page() -> rx.Component:
    return protected_workspace(
        Role.MEDICO,
        page_header(
            "Atendimento",
            "Fila médica",
            "Chame o próximo paciente elegível e finalize somente o atendimento associado à sua sessão.",
        ),
        feedback_region(
            DoctorQueueState.error_message,
            DoctorQueueState.success_message,
        ),
        doctor_waiting_summary(),
        rx.cond(
            DoctorQueueState.is_loading,
            rx.center(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text(
                        "Carregando atendimento…",
                        color="var(--vitta-text-muted)",
                        size="2",
                    ),
                    spacing="2",
                    align="center",
                ),
                min_height="13rem",
                width="100%",
                role="status",
                aria_live="polite",
            ),
            doctor_active_panel(),
        ),
        active="atendimento",
    )


def finance_page() -> rx.Component:
    return dashboard_shell(
        Role.FINANCEIRO,
        "Financeiro",
        "O acesso financeiro está validado. Pagamentos, valores e integração com Asaas sandbox serão implementados em change própria.",
    )


def admin_reception_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/recepcao",
        "recepcao",
        reception_preview(),
    )


def admin_agenda_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/agenda",
        "agenda",
        agenda_preview(),
    )


def admin_clinical_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/atendimento",
        "atendimento",
        clinical_preview(),
    )


def admin_patients_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/pacientes",
        "pacientes",
        patients_preview(),
    )


def admin_finance_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/financeiro",
        "financeiro",
        finance_preview(),
    )


def forbidden_page() -> rx.Component:
    """Render an authenticated 403-style route without disclosing another role's content."""
    content = rx.center(
        rx.box(
            brand_logo(width="8.5rem"),
            rx.box(
                rx.text(
                    "403 · ACESSO RESTRITO",
                    font_size="0.72rem",
                    font_weight="800",
                    letter_spacing="0.09em",
                    color="var(--vitta-primary)",
                ),
                rx.heading(
                    "Esta área pertence a outra função.",
                    size="8",
                    letter_spacing="-0.035em",
                    font_family="var(--vitta-font-display)",
                    margin_top="0.6rem",
                ),
                rx.text(
                    "Sua sessão continua ativa. Volte ao ambiente compatível com sua função para continuar.",
                    color="var(--vitta-text-muted)",
                    line_height="1.65",
                    max_width="46ch",
                    margin_top="0.7rem",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("arrow_left", size=17),
                        rx.text("Voltar ao meu painel"),
                        spacing="2",
                        align="center",
                    ),
                    size="3",
                    color_scheme="teal",
                    high_contrast=True,
                    on_click=AuthState.go_to_dashboard,
                    margin_top="1.4rem",
                ),
                margin_top="1.5rem",
            ),
            width="min(100%, 37rem)",
            padding=rx.breakpoints(initial="1.5rem", sm="2.25rem"),
            border="1px solid var(--vitta-border)",
            border_radius="var(--vitta-radius-large)",
            background="var(--vitta-surface)",
            box_shadow="var(--vitta-shadow-sm)",
        ),
        width="100%",
        min_height="100dvh",
        padding="1.25rem",
        background="var(--vitta-canvas)",
    )

    return rx.cond(
        AuthState.auth_checked & (AuthState.current_role != ""),
        content,
        loading_surface(),
    )
