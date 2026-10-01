"""Vitta-One public and protected page components."""

import reflex as rx

from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState
from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState
from vitta_one.ui.admin_experience import admin_experience
from vitta_one.ui.components import (
    brand_logo,
    brand_mark,
    dashboard_shell,
    loading_surface,
    login_form,
    protected_admin_surface,
    protected_workspace,
)
from vitta_one.ui.queue_components import (
    active_queue_panel,
    doctor_active_panel,
    doctor_waiting_summary,
    enqueue_panel,
    feedback_region,
    patient_identity_panel,
    reassess_panel,
    withdraw_panel,
)


def root_page() -> rx.Component:
    """Render only a neutral routing surface while the session is resolved."""
    return loading_surface("Abrindo o Vitta-One…")


def login_page() -> rx.Component:
    """Render the public Vitta-One authentication entry point."""
    content = rx.center(
        rx.flex(
            rx.box(
                rx.vstack(
                    brand_logo(width="11.25rem"),
                    rx.box(
                        rx.text(
                            "ACESSO INTERNO",
                            font_size="0.72rem",
                            font_weight="800",
                            letter_spacing="0.12em",
                            color="var(--vitta-primary)",
                        ),
                        rx.heading(
                            "Bem-vindo de volta",
                            size="8",
                            margin_top="0.45rem",
                            letter_spacing="-0.045em",
                            line_height="1.08",
                            color="var(--vitta-text)",
                        ),
                        rx.text(
                            "Entre com as credenciais fornecidas pela clínica para acessar seu ambiente de trabalho.",
                            margin_top="0.7rem",
                            color="var(--vitta-text-muted)",
                            line_height="1.65",
                            max_width="40ch",
                        ),
                        width="100%",
                    ),
                    login_form(),
                    rx.hstack(
                        rx.icon("lock_keyhole", size=15, color="var(--vitta-primary)"),
                        rx.text(
                            "Sessão protegida e permissões revalidadas no servidor.",
                            size="1",
                            color="var(--vitta-text-muted)",
                            line_height="1.45",
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                        justify="center",
                    ),
                    spacing="6",
                    align="stretch",
                    width="100%",
                ),
                class_name="vitta-login-form-panel",
            ),
            rx.box(
                rx.image(
                    src="/vitta-one-clinician.webp",
                    alt="Profissional de saúde em ambiente clínico",
                    class_name="vitta-login-clinician-image",
                    width="100%",
                    height="100%",
                    object_fit="cover",
                    object_position="center",
                ),
                rx.box(
                    rx.hstack(
                        rx.box(rx.icon("shield_check", size=19), class_name="vitta-login-note-icon"),
                        rx.box(
                            rx.text("Ambiente clínico seguro", font_weight="800", size="2"),
                            rx.text(
                                "A interface libera somente o que a função autenticada pode acessar.",
                                size="1",
                                color="var(--vitta-text-muted)",
                                line_height="1.45",
                                margin_top="0.18rem",
                            ),
                        ),
                        spacing="3",
                        align="start",
                    ),
                    class_name="vitta-login-image-note",
                ),
                class_name="vitta-login-image-panel",
            ),
            class_name="vitta-login-shell",
            width="100%",
        ),
        width="100%",
        min_height="100dvh",
        padding=rx.breakpoints(initial="0", md="1.5rem"),
        background="var(--vitta-canvas)",
    )

    return rx.cond(
        AuthState.auth_checked & (AuthState.current_role == ""),
        content,
        loading_surface(),
    )


def admin_page() -> rx.Component:
    return protected_admin_surface(admin_experience())


def reception_page() -> rx.Component:
    return protected_workspace(
        Role.RECEPCIONISTA,
        rx.box(
            rx.heading("Recepção e fila de atendimento", size="8", letter_spacing="-0.03em"),
            rx.text(
                "Cadastre ou localize o paciente, registre a prioridade recebida e acompanhe a fila ativa.",
                color="var(--vitta-text-muted)",
                max_width="68ch",
                line_height="1.65",
                margin_top="0.45rem",
            ),
            width="100%",
        ),
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
    )


def doctor_page() -> rx.Component:
    return protected_workspace(
        Role.MEDICO,
        rx.box(
            rx.heading("Fila médica", size="8", letter_spacing="-0.03em"),
            rx.text(
                "Chame o próximo paciente elegível e finalize somente o atendimento associado à sua sessão.",
                color="var(--vitta-text-muted)",
                max_width="68ch",
                line_height="1.65",
                margin_top="0.45rem",
            ),
            width="100%",
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
    )


def finance_page() -> rx.Component:
    return dashboard_shell(
        Role.FINANCEIRO,
        "Painel financeiro",
        "O acesso financeiro está validado. Pagamentos, valores e operações com Asaas sandbox serão implementados em changes próprias.",
    )


def forbidden_page() -> rx.Component:
    """Render an authenticated 403-style route without disclosing another role's content."""
    content = rx.center(
        rx.vstack(
            brand_mark(),
            rx.text("403", font_weight="800", color="var(--vitta-primary)", letter_spacing="0.08em"),
            rx.heading("Acesso não autorizado", size="8", text_align="center", letter_spacing="-0.03em"),
            rx.text(
                "Sua sessão está ativa, mas esta área pertence a outra função da clínica.",
                color="var(--vitta-text-muted)",
                line_height="1.7",
                text_align="center",
                max_width="42ch",
            ),
            rx.button(
                "Voltar ao meu painel",
                size="3",
                color_scheme="teal",
                high_contrast=True,
                on_click=AuthState.go_to_dashboard,
            ),
            spacing="5",
            align="center",
            padding=rx.breakpoints(initial="2rem 1.25rem", sm="3rem"),
            max_width="36rem",
            border="1px solid var(--vitta-border)",
            border_radius="var(--vitta-radius-panel)",
            background="var(--vitta-surface)",
            box_shadow="var(--vitta-shadow-panel)",
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
