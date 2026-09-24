"""Vitta-One public and protected page components."""

import reflex as rx

from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState
from vitta_one.ui.components import brand_mark, dashboard_shell, loading_surface, login_form


def root_page() -> rx.Component:
    """Render only a neutral routing surface while the session is resolved."""
    return loading_surface("Abrindo o Vitta-One…")


def login_page() -> rx.Component:
    """Render the public Vitta-One authentication entry point."""
    content = rx.center(
        rx.flex(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        brand_mark(),
                        rx.text("Vitta-One", font_weight="800", font_size="1.05rem"),
                        spacing="3",
                        align="center",
                    ),
                    rx.box(
                        rx.text(
                            "Acesso clínico, sem ruído.",
                            font_size=rx.breakpoints(initial="2rem", sm="2.7rem"),
                            font_weight="760",
                            letter_spacing="-0.045em",
                            line_height="1.05",
                            max_width="11ch",
                        ),
                        rx.text(
                            "Identidade e permissões são validadas no servidor antes de qualquer área protegida ser liberada.",
                            margin_top="1rem",
                            max_width="42ch",
                            line_height="1.7",
                            color="var(--vitta-text-muted)",
                        ),
                    ),
                    rx.hstack(
                        rx.box(
                            width="2.8rem",
                            height="2px",
                            background="var(--vitta-primary)",
                            aria_hidden="true",
                        ),
                        rx.text("Ambiente interno", size="2", color="var(--vitta-text-muted)"),
                        spacing="3",
                        align="center",
                    ),
                    spacing="7",
                    align="start",
                    height="100%",
                    justify="between",
                ),
                flex="1 1 0",
                padding=rx.breakpoints(initial="1.5rem", md="3.5rem"),
                background="var(--vitta-surface-muted)",
                border_radius=rx.breakpoints(
                    initial="var(--vitta-radius-panel) var(--vitta-radius-panel) 0 0",
                    md="var(--vitta-radius-panel) 0 0 var(--vitta-radius-panel)",
                ),
                min_height=rx.breakpoints(initial="auto", md="35rem"),
            ),
            rx.center(
                rx.box(
                    rx.vstack(
                        rx.box(
                            rx.text("Identificação", font_size="0.78rem", font_weight="800", letter_spacing="0.08em", color="var(--vitta-primary)"),
                            rx.heading("Entrar no sistema", size="7", margin_top="0.35rem", letter_spacing="-0.03em"),
                            rx.text(
                                "Use as credenciais fornecidas pela administração da clínica.",
                                margin_top="0.55rem",
                                color="var(--vitta-text-muted)",
                                line_height="1.6",
                            ),
                            width="100%",
                        ),
                        login_form(),
                        spacing="6",
                        width="100%",
                    ),
                    width="100%",
                    max_width="27rem",
                    padding=rx.breakpoints(initial="1.5rem", sm="2.5rem"),
                ),
                flex="1 1 0",
                background="var(--vitta-surface)",
                border_radius=rx.breakpoints(
                    initial="0 0 var(--vitta-radius-panel) var(--vitta-radius-panel)",
                    md="0 var(--vitta-radius-panel) var(--vitta-radius-panel) 0",
                ),
                min_height=rx.breakpoints(initial="auto", md="35rem"),
            ),
            width="100%",
            max_width="70rem",
            direction=rx.breakpoints(initial="column", md="row"),
            box_shadow="var(--vitta-shadow-panel)",
            border="1px solid var(--vitta-border)",
            border_radius="var(--vitta-radius-panel)",
            overflow="hidden",
        ),
        width="100%",
        min_height="100dvh",
        padding=rx.breakpoints(initial="1rem", sm="2rem"),
        background="var(--vitta-canvas)",
    )

    return rx.cond(
        AuthState.auth_checked & (AuthState.current_role == ""),
        content,
        loading_surface(),
    )


def admin_page() -> rx.Component:
    return dashboard_shell(
        Role.ADMINISTRADOR,
        "Painel administrativo",
        "O acesso administrativo está validado. Gestão de usuários, profissionais, especialidades e configurações será implementada em changes próprias.",
    )


def reception_page() -> rx.Component:
    return dashboard_shell(
        Role.RECEPCIONISTA,
        "Painel de recepção",
        "O acesso da recepção está validado. Pacientes, agenda, agendamentos e estados de consulta serão implementados em changes próprias.",
    )


def doctor_page() -> rx.Component:
    return dashboard_shell(
        Role.MEDICO,
        "Painel médico",
        "O acesso médico está validado. Atendimento, histórico clínico, diagnósticos, prescrições e exames serão implementados em changes próprias.",
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
