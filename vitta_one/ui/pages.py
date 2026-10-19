"""Vitta-One public, protected, and local QA page components."""

import reflex as rx

from vitta_one.appointment_scheduling.state import AdminAvailabilityState, ReceptionAgendaState
from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState
from vitta_one.doctor_workspace.state import DoctorWorkspaceState
from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState
from vitta_one.patient_portal.state import PatientPortalState
from vitta_one.professional_directory.state import AdminDirectoryState
from vitta_one.reception.dashboard.components import reception_dashboard
from vitta_one.ui.admin_directory_components import (
    admin_directory_workspace,
    specialties_management_workspace,
    professionals_management_workspace,
)
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
    empty_state,
    feedback_region,
    loading_surface,
    login_form,
    page_header,
    protected_workspace,
    field_label,
    section_panel,
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
from vitta_one.ui.workspace_components import (
    admin_clinic_configuration,
    doctor_calendar,
    doctor_consultation_list,
    doctor_patient_list,
    patient_calendar,
    patient_clinic_location,
    patient_consultation_list,
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


def patient_activation_page() -> rx.Component:
    """Public activation form posts directly to a native ASGI endpoint."""
    return rx.box(
        rx.vstack(
            brand_logo(width="9rem"),
            page_header(
                "Ativação de acesso",
                "Ative seu portal",
                "Use o código enviado pela Recepção e escolha uma senha para acessar seu portal de pronto atendimento.",
            ),
            section_panel(
                rx.el.form(
                    rx.vstack(
                        rx.box(
                            field_label("E-mail do convite", "patient-activation-email"),
                            rx.el.input(
                                id="patient-activation-email",
                                name="email",
                                type="email",
                                auto_complete="email",
                                required=True,
                                max_length=320,
                                class_name="vitta-input",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.box(
                            field_label("Código de ativação", "patient-activation-code"),
                            rx.el.input(
                                id="patient-activation-code",
                                name="code",
                                type="text",
                                auto_complete="one-time-code",
                                required=True,
                                max_length=128,
                                class_name="vitta-input",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.box(
                            field_label("Nova senha", "patient-activation-password"),
                            rx.el.input(
                                id="patient-activation-password",
                                name="password",
                                type="password",
                                auto_complete="new-password",
                                required=True,
                                min_length=12,
                                max_length=128,
                                class_name="vitta-input",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.text("Use pelo menos 12 caracteres. A senha não é enviada ao estado Reflex.", size="1", color="var(--vitta-text-muted)"),
                        rx.button("Ativar acesso", type="submit", width="100%", min_height="2.8rem", color_scheme="teal", high_contrast=True),
                        spacing="4",
                        width="100%",
                        align="stretch",
                    ),
                    action="/api/paciente/ativar",
                    method="post",
                    enc_type="application/x-www-form-urlencoded",
                    no_validate=True,
                    width="100%",
                )
            ),
            rx.link("Voltar ao login", href="/login", class_name="vitta-context-link"),
            spacing="5",
            width="100%",
            max_width="42rem",
            align="stretch",
            margin="0 auto",
        ),
        class_name="vitta-page",
        min_height="100vh",
        padding="2rem 1rem",
    )

def first_access_page() -> rx.Component:
    """Provisional doctors must rotate an initial password before clinical access."""
    content = rx.center(
        rx.box(
            rx.vstack(
                brand_logo(width="9rem"),
                rx.heading("Defina sua nova senha", size="7"),
                rx.text(
                    "Por segurança, escolha uma senha definitiva para continuar.",
                    color="var(--vitta-text-muted)", line_height="1.5",
                ),
                rx.el.form(
                    rx.vstack(
                        rx.box(
                            rx.el.label("Senha temporária", html_for="first-access-current"),
                            rx.el.input(
                                id="first-access-current", name="current_password",
                                type="password", required=True,
                                auto_complete="current-password", class_name="vitta-input",
                            ), width="100%",
                        ),
                        rx.box(
                            rx.el.label("Nova senha (mínimo 12 caracteres)",
                                        html_for="first-access-new"),
                            rx.el.input(
                                id="first-access-new", name="new_password",
                                type="password", required=True,
                                auto_complete="new-password", min_length=12,
                                class_name="vitta-input",
                            ), width="100%",
                        ),
                        rx.box(
                            rx.el.label("Confirme a nova senha",
                                        html_for="first-access-confirm"),
                            rx.el.input(
                                id="first-access-confirm", name="confirm_password",
                                type="password", required=True,
                                auto_complete="new-password", class_name="vitta-input",
                            ), width="100%",
                        ),
                        rx.cond(
                            AuthState.first_access_error != "",
                            rx.callout(
                                AuthState.first_access_error, color_scheme="red",
                                role="alert",
                            ),
                            rx.fragment(),
                        ),
                        rx.button(
                            "Salvar nova senha", type="submit", width="100%",
                            loading=AuthState.is_submitting,
                            disabled=AuthState.is_submitting,
                            color_scheme="teal", size="3",
                        ),
                        spacing="4", width="100%", align="stretch",
                    ),
                    on_submit=AuthState.save_first_access,
                    no_validate=True, width="100%",
                ),
                rx.button("Sair", type="button", variant="ghost",
                          on_click=AuthState.logout),
                spacing="4", width="100%", align="stretch",
            ),
            padding=rx.breakpoints(initial="1.25rem", sm="2rem"),
            width="100%", max_width="30rem",
            border="1px solid var(--vitta-border)",
            border_radius="var(--vitta-radius-panel)",
            background="var(--vitta-surface)",
        ),
        min_height="100dvh", width="100%", padding="1rem",
        background="var(--vitta-canvas)",
    )
    return rx.cond(
        AuthState.auth_checked
        & (AuthState.current_role == Role.MEDICO.value)
        & (AuthState.verified_path == "/primeiro-acesso"),
        content,
        loading_surface(),
    )


def admin_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        admin_clinic_configuration(),
        admin_directory_workspace(),
        active="administracao",
    )


def admin_specialties_page() -> rx.Component:
    """Administrator-only full specialty directory."""
    return protected_workspace(
        Role.ADMINISTRADOR,
        specialties_management_workspace(),
        active="administracao",
        verified_path="/admin/especialidades",
    )


def admin_professionals_page() -> rx.Component:
    """Administrator-only full professional directory."""
    return protected_workspace(
        Role.ADMINISTRADOR,
        professionals_management_workspace(),
        active="administracao",
        verified_path="/admin/profissionais",
    )


def reception_page() -> rx.Component:
    """Entrada operacional do pronto-socorro: somente pacientes e fila real."""
    return protected_workspace(
        Role.RECEPCIONISTA,
        page_header(
            "Pronto-socorro",
            "Fila de atendimento",
            "Acompanhe pacientes aguardando e organize a chegada de novos pacientes.",
        ),
        feedback_region(
            ReceptionQueueState.error_message,
            ReceptionQueueState.success_message,
        ),
        rx.flex(
            rx.link(
                "Cadastrar ou localizar paciente",
                href="/recepcao/pacientes",
                class_name="vitta-context-link",
            ),
            rx.link(
                "Gerenciar fila e reavaliações",
                href="/recepcao/fila",
                class_name="vitta-context-link",
            ),
            gap="3",
            flex_wrap="wrap",
        ),
        active_queue_panel(),
        active="recepcao",
    )

def reception_agenda_page() -> rx.Component:
    """Scheduling, rescheduling, cancellation and check-in; preserved services."""
    return protected_workspace(
        Role.RECEPCIONISTA,
        page_header(
            "Agenda",
            "Agenda e check-in",
            "Consulte horários por profissional, agende, reagende e confirme a chegada.",
        ),
        reception_agenda_panel(),
        active="agenda",
        verified_path="/recepcao/agenda",
    )


def reception_patients_page() -> rx.Component:
    """Existing patient creation and lookup, now accessible as its own workspace."""
    return protected_workspace(
        Role.RECEPCIONISTA,
        page_header(
            "Pacientes",
            "Cadastro e localização",
            "Identifique um paciente existente pelo CPF ou cadastre com validação.",
        ),
        feedback_region(
            ReceptionQueueState.error_message,
            ReceptionQueueState.success_message,
        ),
        patient_identity_panel(),
        enqueue_panel(),
        rx.link("Acompanhar fila de espera", href="/recepcao/fila",
                class_name="vitta-context-link"),
        active="pacientes",
        verified_path="/recepcao/pacientes",
    )


def reception_queue_page() -> rx.Component:
    """Reception queue, walk-in entry, re-evaluation and withdrawal."""
    return protected_workspace(
        Role.RECEPCIONISTA,
        page_header(
            "Fila",
            "Fila de espera",
            "Acompanhe prioridades informadas, entradas avulsas, reavaliações e retiradas.",
        ),
        feedback_region(
            ReceptionQueueState.error_message,
            ReceptionQueueState.success_message,
        ),
        rx.flex(
            patient_identity_panel(),
            enqueue_panel(),
            direction=rx.breakpoints(initial="column", xl="row"),
            gap="1rem", align="start", width="100%",
        ),
        active_queue_panel(),
        reassess_panel(),
        withdraw_panel(),
        active="fila",
        verified_path="/recepcao/fila",
    )


def doctor_page() -> rx.Component:
    return protected_workspace(
        Role.MEDICO,
        page_header(
            "Atendimento",
            "Pronto atendimento",
            "Chame pacientes por prioridade e ordem de chegada, registre a evolução e finalize seu próprio atendimento.",
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


def doctor_agenda_page() -> rx.Component:
    return protected_workspace(
        Role.MEDICO,
        page_header(
            "Agenda médica",
            "Minha agenda",
            "Consultas relacionadas ao profissional associado à sua conta, com datas no fuso da clínica.",
        ),
        feedback_region(DoctorWorkspaceState.error_message, "", "doctor-agenda-feedback"),
        rx.link("Abrir fila e atendimento clínico", href="/medico", class_name="vitta-context-link"),
        doctor_calendar(),
        doctor_consultation_list(),
        active="agenda-medica",
        verified_path="/medico/agenda",
    )


def doctor_patients_page() -> rx.Component:
    return protected_workspace(
        Role.MEDICO,
        page_header(
            "Pacientes",
            "Pacientes vinculados",
            "Pessoas derivadas exclusivamente de consultas do seu cadastro profissional.",
        ),
        feedback_region(DoctorWorkspaceState.error_message, "", "doctor-patients-feedback"),
        doctor_patient_list(),
        active="pacientes-medico",
        verified_path="/medico/pacientes",
    )


def patient_portal_page() -> rx.Component:
    """Honest queue-only portal until authorized attendance history is implemented."""
    return protected_workspace(
        Role.PACIENTE,
        page_header(
            "Pronto atendimento",
            "Meus atendimentos",
            "O pronto-socorro funciona por ordem de chegada e prioridade informada; não há agendamentos.",
        ),
        section_panel(
            empty_state(
                "clipboard_list",
                "Histórico ainda não disponível",
                "A consulta aos atendimentos realizados será disponibilizada após vinculação segura do histórico da fila à conta do paciente.",
            )
        ),
        active="consultas-paciente",
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
