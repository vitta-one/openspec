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
            spacing="3",
            align="center",
        ),
        class_name="vitta-admin-topbar",
        justify="between",
        align="center",
        width="100%",
    )


def _module_card(
    title: str,
    description: str,
    icon: str,
    section: str,
    status: str,
    tone: str,
) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(rx.icon(icon, size=20), class_name="vitta-module-icon"),
            _status_pill(status, tone),
            justify="between",
            align="start",
            width="100%",
        ),
        rx.heading(title, size="4", margin_top="1rem", letter_spacing="-0.02em"),
        rx.text(
            description,
            size="2",
            color="var(--vitta-text-muted)",
            line_height="1.55",
            margin_top="0.45rem",
            min_height="3rem",
        ),
        rx.button(
            "Abrir módulo",
            rx.icon("arrow_right", size=16),
            type="button",
            variant="ghost",
            color_scheme="teal",
            on_click=AdminExperienceState.open_section(section),
            margin_top="1rem",
            padding_left="0",
        ),
        class_name="vitta-module-card",
    )


def _overview() -> rx.Component:
    return rx.vstack(
        _section_heading(
            "Central administrativa",
            "Boa noite. O Vitta-One está pronto para revisão.",
            "Este hub reúne a administração real já implementada e prévias navegáveis dos fluxos anexados. As prévias são isoladas de dados clínicos reais e não enfraquecem a autorização server-side.",
        ),
        rx.box(
            rx.flex(
                rx.box(
                    rx.hstack(
                        rx.icon("shield_check", size=20, color="var(--vitta-primary)"),
                        rx.text("Acesso administrativo validado", font_weight="750"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Diretório de profissionais e especialidades permanece conectado aos dados persistidos. Os demais módulos abaixo funcionam como fluxo visual para aprovação de UI/UX.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        line_height="1.55",
                        margin_top="0.45rem",
                    ),
                    max_width="72ch",
                ),
                rx.image(
                    src="/vitta-one-mark.webp",
                    alt="",
                    width="4.5rem",
                    height="4.5rem",
                    object_fit="contain",
                    aria_hidden="true",
                    class_name="vitta-overview-mark",
                ),
                justify="between",
                align="center",
                width="100%",
                gap="1.5rem",
            ),
            class_name="vitta-admin-hero",
        ),
        rx.box(
            _module_card(
                "Recepção",
                "Agenda do dia, status de chegada, próximos atendimentos e atalhos de balcão.",
                "clipboard_plus",
                "recepcao",
                "Prévia visual",
                "info",
            ),
            _module_card(
                "Agenda",
                "Visão semanal com horários, detalhes da consulta e transição visual para atendimento.",
                "calendar_days",
                "agenda",
                "Prévia visual",
                "info",
            ),
            _module_card(
                "Atendimento clínico",
                "Estrutura de anamnese, diagnóstico, conduta, prescrição e exames sem persistência nesta etapa.",
                "stethoscope",
                "atendimento",
                "Prévia visual",
                "info",
            ),
            _module_card(
                "Pacientes",
                "Perfil longitudinal com abas e timeline clínica demonstrativa.",
                "users",
                "pacientes",
                "Prévia visual",
                "info",
            ),
            _module_card(
                "Financeiro",
                "Estado honesto da área financeira enquanto Asaas e pagamentos seguem para change própria.",
                "wallet_cards",
                "financeiro",
                "Planejado",
                "warning",
            ),
            _module_card(
                "Administração",
                "Profissionais e especialidades usando o fluxo funcional e persistido já existente.",
                "settings",
                "administracao",
                "Funcional",
                "success",
            ),
            class_name="vitta-module-grid",
        ),
        spacing="5",
        align="stretch",
        width="100%",
    )


def _demo_stat(label: str, value: str, helper: str, icon: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(rx.icon(icon, size=18), class_name="vitta-module-icon vitta-module-icon--small"),
            rx.text(label, size="1", color="var(--vitta-text-muted)"),
            spacing="2",
            align="center",
        ),
        rx.text(value, font_size="1.65rem", font_weight="800", margin_top="0.65rem"),
        rx.text(helper, size="1", color="var(--vitta-text-muted)", margin_top="0.25rem"),
        class_name="vitta-demo-stat",
    )


def _appointment_row(
    time: str,
    patient: str,
    professional: str,
    specialty: str,
    status: str,
    tone: str,
    action: str,
) -> rx.Component:
    return rx.flex(
        rx.box(
            rx.text(time, font_weight="800", font_size="0.95rem"),
            rx.text("DEMO", size="1", color="var(--vitta-text-muted)"),
            min_width="4.7rem",
        ),
        rx.box(
            rx.text(patient, font_weight="750", size="2"),
            rx.text(
                professional,
                " · ",
                specialty,
                size="1",
                color="var(--vitta-text-muted)",
                margin_top="0.2rem",
            ),
            flex="1 1 15rem",
        ),
        _status_pill(status, tone),
        rx.button(
            action,
            type="button",
            size="2",
            variant="outline",
            color_scheme="teal",
            on_click=AdminExperienceState.open_section("agenda"),
        ),
        class_name="vitta-demo-table-row",
        align="center",
        width="100%",
        gap="1rem",
    )


def _reception_preview() -> rx.Component:
    return rx.vstack(
        _section_heading(
            "Recepção",
            "Operação do dia em uma única leitura.",
            "Uma composição inspirada nas telas anexadas, priorizando fila visual, status textual e acesso rápido ao detalhe da agenda.",
        ),
        _preview_notice(),
        rx.box(
            _demo_stat("Consultas demonstradas", "08", "Amostra visual do período", "calendar_days"),
            _demo_stat("Aguardando", "03", "Exemplo de estado operacional", "clock_3"),
            _demo_stat("Em atendimento", "02", "Sem vínculo com fila real", "stethoscope"),
            _demo_stat("Finalizadas", "03", "Somente para composição", "circle_check"),
            class_name="vitta-demo-stat-grid",
        ),
        rx.box(
