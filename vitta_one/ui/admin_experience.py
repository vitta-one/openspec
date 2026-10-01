"""Premium administrator experience and visual previews for Vitta-One."""

import reflex as rx

from vitta_one.auth.state import AuthState
from vitta_one.ui.admin_directory_components import admin_directory_workspace


class AdminExperienceState(rx.State):
    """Local-only navigation state for the administrator visual workspace."""

    active_section: str = "inicio"
    patient_tab: str = "historico"

    @rx.event
    def open_section(self, section: str) -> None:
        self.active_section = section

    @rx.event
    def open_patient_history(self) -> None:
        self.active_section = "pacientes"
        self.patient_tab = "historico"

    @rx.event
    def open_attendance_preview(self) -> None:
        self.active_section = "atendimento"

    @rx.event
    def set_patient_tab(self, tab: str) -> None:
        self.patient_tab = tab


def _preview_notice() -> rx.Component:
    return rx.hstack(
        rx.icon("flask_conical", size=18, color="var(--vitta-primary)"),
        rx.box(
            rx.text(
                "Prévia visual do fluxo",
                font_weight="750",
                color="var(--vitta-text)",
                size="2",
            ),
            rx.text(
                "Os dados desta área são demonstrativos e não são gravados no prontuário nem executam operações clínicas.",
                color="var(--vitta-text-muted)",
                size="1",
                line_height="1.5",
                margin_top="0.1rem",
            ),
        ),
        spacing="3",
        align="start",
        width="100%",
        padding="0.8rem 0.9rem",
        background="var(--vitta-primary-soft)",
        border="1px solid var(--vitta-border)",
        border_radius="var(--vitta-radius-control)",
        role="status",
        aria_live="polite",
    )


def _section_heading(eyebrow: str, title: str, description: str) -> rx.Component:
    return rx.box(
        rx.text(
            eyebrow.upper(),
            font_size="0.72rem",
            font_weight="800",
            letter_spacing="0.1em",
            color="var(--vitta-primary)",
        ),
        rx.heading(
            title,
            size="7",
            margin_top="0.3rem",
            letter_spacing="-0.035em",
            color="var(--vitta-text)",
        ),
        rx.text(
            description,
            color="var(--vitta-text-muted)",
            line_height="1.65",
            margin_top="0.45rem",
            max_width="72ch",
        ),
        width="100%",
    )


def _status_pill(label: str, tone: str = "neutral") -> rx.Component:
    classes = {
        "success": "vitta-demo-pill vitta-demo-pill--success",
        "info": "vitta-demo-pill vitta-demo-pill--info",
        "warning": "vitta-demo-pill vitta-demo-pill--warning",
        "neutral": "vitta-demo-pill",
    }
    return rx.text(label, class_name=classes.get(tone, classes["neutral"]))


def _nav_button(label: str, icon: str, section: str) -> rx.Component:
    selected = AdminExperienceState.active_section == section
    return rx.button(
        rx.icon(icon, size=18),
        rx.text(label, white_space="nowrap"),
        type="button",
        variant="ghost",
        class_name=rx.cond(
            selected,
            "vitta-admin-nav-item vitta-admin-nav-item--active",
            "vitta-admin-nav-item",
        ),
        on_click=AdminExperienceState.open_section(section),
        aria_label=f"Abrir {label}",
    )


def _brand_block() -> rx.Component:
    return rx.box(
        rx.image(
            src="/vitta-one-logo.webp",
            alt="Vitta-One",
            width="10.5rem",
            height="auto",
            display="block",
        ),
        rx.text(
            "CLINICAL CARE",
            font_size="0.63rem",
            font_weight="800",
            letter_spacing="0.18em",
            color="var(--vitta-text-muted)",
            margin_top="0.25rem",
            margin_left="3.35rem",
        ),
        width="100%",
    )


def _desktop_sidebar() -> rx.Component:
    return rx.box(
        _brand_block(),
        rx.vstack(
            _nav_button("Visão geral", "layout_dashboard", "inicio"),
            _nav_button("Recepção", "clipboard_plus", "recepcao"),
            _nav_button("Agenda", "calendar_days", "agenda"),
            _nav_button("Atendimento clínico", "stethoscope", "atendimento"),
            _nav_button("Pacientes", "users", "pacientes"),
            _nav_button("Financeiro", "wallet_cards", "financeiro"),
            _nav_button("Administração", "settings", "administracao"),
            spacing="1",
            align="stretch",
            width="100%",
            margin_top="2.4rem",
        ),
        rx.box(
            rx.text("ADMIN LOCAL", class_name="vitta-admin-sidebar-kicker"),
            rx.text(
                "Hub visual com acesso às prévias de todos os fluxos sem alterar o RBAC das operações clínicas.",
                size="1",
                line_height="1.5",
                color="var(--vitta-text-muted)",
                margin_top="0.4rem",
            ),
            margin_top="auto",
            padding_top="2rem",
        ),
        class_name="vitta-admin-sidebar",
    )


def _mobile_navigation() -> rx.Component:
    return rx.box(
        rx.hstack(
            _nav_button("Visão geral", "layout_dashboard", "inicio"),
            _nav_button("Recepção", "clipboard_plus", "recepcao"),
            _nav_button("Agenda", "calendar_days", "agenda"),
            _nav_button("Atendimento", "stethoscope", "atendimento"),
            _nav_button("Pacientes", "users", "pacientes"),
            _nav_button("Financeiro", "wallet_cards", "financeiro"),
            _nav_button("Administração", "settings", "administracao"),
            spacing="2",
            width="max-content",
        ),
        class_name="vitta-admin-mobile-nav",
        aria_label="Navegação do administrador",
    )


def _topbar() -> rx.Component:
    return rx.flex(
        rx.hstack(
            rx.box(
                rx.text("Unidade", size="1", color="var(--vitta-text-muted)"),
                rx.text("Clínica Vitta-One", size="2", font_weight="700"),
            ),
            rx.hstack(
                rx.box(class_name="vitta-system-dot", aria_hidden="true"),
                rx.text("Sistema operacional", size="1", color="var(--vitta-text-muted)"),
                spacing="2",
                align="center",
            ),
            spacing="5",
            align="center",
        ),
        rx.hstack(
            rx.vstack(
                rx.text(AuthState.current_email, size="2", font_weight="700"),
                rx.text("Administrador local", size="1", color="var(--vitta-text-muted)"),
                spacing="0",
                align="end",
            ),
            rx.button(
                rx.icon("log_out", size=18),
                type="button",
                variant="outline",
                color_scheme="teal",
                class_name="vitta-icon-action",
                on_click=AuthState.logout,
                aria_label="Sair do Vitta-One",
            ),
