"""Task-oriented administration navigation, without duplicating business actions."""

import reflex as rx

from vitta_one.ui.components import page_header, section_panel


def _admin_destination(title: str, description: str, href: str, icon: str) -> rx.Component:
    """A semantic navigation link with an explicit destination and a large target."""
    return rx.link(
        rx.flex(
            rx.box(rx.icon(icon, size=20), class_name="vitta-admin-action-icon"),
            rx.vstack(
                rx.text(title, font_weight="750", color="var(--vitta-text)", size="3"),
                rx.text(description, size="2", color="var(--vitta-text-muted)", line_height="1.5"),
                spacing="1", align="start", flex="1", min_width="0",
            ),
            rx.icon("chevron_right", size=19, color="var(--vitta-text-muted)", flex_shrink="0"),
            align="center", gap="3", width="100%",
        ),
        href=href,
        class_name="vitta-admin-action",
        aria_label=f"{title}. {description}",
    )


def admin_hub_workspace() -> rx.Component:
    """The admin landing screen routes to one task instead of rendering all forms."""
    return rx.vstack(
        page_header(
            "Administração",
            "Gestão da clínica",
            "Selecione o que precisa fazer. Cada operação tem seu próprio espaço.",
        ),
        section_panel(
            rx.vstack(
                rx.heading("Equipe e acessos", size="4", color="var(--vitta-text)"),
                _admin_destination(
                    "Criar funcionário",
                    "Escolha entre Médico e Recepcionista antes de preencher o cadastro.",
                    "/admin/funcionarios", "user_plus",
                ),
                _admin_destination(
                    "Gerenciar médicos",
                    "Consulte, edite e acompanhe os profissionais cadastrados.",
                    "/admin/profissionais", "stethoscope",
                ),
                _admin_destination(
                    "Especialidades",
                    "Cadastre ou organize as áreas de atendimento.",
                    "/admin/especialidades", "list_filter",
                ),
                rx.divider(),
                rx.heading("Agenda e clínica", size="4", color="var(--vitta-text)"),
                _admin_destination(
                    "Gerenciar horários",
                    "Configure o expediente, horários avulsos e consulte a disponibilidade.",
                    "/admin/horarios", "calendar_clock",
                ),
                _admin_destination(
                    "Configurações da clínica",
                    "Atualize os dados de funcionamento disponíveis para os pacientes.",
                    "/admin/configuracoes", "settings",
                ),
                spacing="2", align="stretch", width="100%",
            ),
            padding=rx.breakpoints(initial="0.85rem", sm="1.25rem"),
        ),
        spacing="4", align="stretch", width="100%",
    )


def admin_staff_type_workspace() -> rx.Component:
    """Step 1 of staff creation: choose a supported profile."""
    return rx.vstack(
        page_header(
            "Administração / Funcionários",
            "Qual perfil deseja cadastrar?",
            "Escolha o tipo de funcionário para abrir o formulário correto.",
        ),
        rx.link("← Voltar à administração", href="/admin", class_name="vitta-text-link"),
        section_panel(
            rx.vstack(
                _admin_destination(
                    "Médico",
                    "Nome, e-mail e especialidades. O acesso respeita o fluxo médico existente.",
                    "/admin/funcionarios/medico", "stethoscope",
                ),
                _admin_destination(
                    "Recepcionista",
                    "E-mail e senha inicial para acessar a operação da recepção.",
                    "/admin/funcionarios/recepcionista", "users",
                ),
                spacing="2", align="stretch", width="100%",
            ),
            padding=rx.breakpoints(initial="0.75rem", sm="1rem"),
        ),
        spacing="4", align="stretch", width="100%",
    )
