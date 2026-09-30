"""Reusable administrator UI for professional and specialty management."""

import reflex as rx

from vitta_one.professional_directory.state import AdminDirectoryState
from vitta_one.ui.components import (
    feedback_region,
    field_label,
    section_panel,
)


def status_badge(is_active, active_label: str, inactive_label: str) -> rx.Component:
    """Show textual status with color only as a secondary cue."""
    return rx.cond(
        is_active,
        rx.badge(active_label, color_scheme="green", high_contrast=True, variant="soft"),
        rx.badge(inactive_label, color_scheme="gray", high_contrast=True, variant="soft"),
    )


def specialty_create_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.box(
                rx.heading("Especialidades", size="5"),
                rx.text(
                    "Cadastre áreas de atuação usadas no diretório de profissionais. Desativar é reversível e não apaga vínculos históricos.",
                    color="var(--vitta-text-muted)",
                    size="2",
                    line_height="1.55",
                    margin_top="0.35rem",
                ),
                width="100%",
            ),
            rx.el.form(
                rx.flex(
                    rx.box(
                        field_label("Nome da especialidade", "specialty-create-name"),
                        rx.el.input(
                            id="specialty-create-name",
                            name="name",
                            type="text",
                            required=True,
                            max_length=120,
                            class_name="vitta-input",
                            aria_describedby=rx.cond(
                                AdminDirectoryState.error_message != "",
                                "admin-feedback",
                                "",
                            ),
                            margin_top="0.4rem",
                        ),
                        flex="1 1 18rem",
                    ),
                    rx.button(
                        "Cadastrar especialidade",
                        type="submit",
                        color_scheme="teal",
                        high_contrast=True,
                        min_height="3rem",
                        disabled=AdminDirectoryState.is_submitting,
                        loading=AdminDirectoryState.is_submitting,
                        flex="0 0 auto",
                    ),
                    direction=rx.breakpoints(initial="column", sm="row"),
                    align=rx.breakpoints(initial="stretch", sm="end"),
                    gap="0.75rem",
                    width="100%",
                ),
                on_submit=AdminDirectoryState.create_specialty,
                reset_on_submit=True,
                width="100%",
            ),
            spacing="4",
            width="100%",
            align="stretch",
        )
    )


def specialty_row(row) -> rx.Component:
    return rx.box(
        rx.cond(
            AdminDirectoryState.editing_specialty_id == row["id"],
            rx.vstack(
                rx.box(
                    field_label("Nome da especialidade", "specialty-edit-name"),
                    rx.el.input(
                        id="specialty-edit-name",
                        type="text",
                        value=AdminDirectoryState.editing_specialty_name,
                        on_change=AdminDirectoryState.update_specialty_edit_name,
                        max_length=120,
                        required=True,
                        class_name="vitta-input",
                        margin_top="0.4rem",
                    ),
                    width="100%",
                ),
                rx.flex(
                    rx.button(
                        "Cancelar",
                        type="button",
                        variant="ghost",
                        on_click=AdminDirectoryState.cancel_specialty_edit,
                        disabled=AdminDirectoryState.is_submitting,
                    ),
                    rx.button(
                        "Salvar nome",
                        type="button",
                        color_scheme="teal",
                        high_contrast=True,
                        on_click=AdminDirectoryState.save_specialty_edit,
                        disabled=AdminDirectoryState.is_submitting,
                        loading=AdminDirectoryState.is_submitting,
                    ),
                    gap="0.5rem",
                    justify="end",
                    direction=rx.breakpoints(initial="column-reverse", sm="row"),
                    width="100%",
                ),
                spacing="3",
                align="stretch",
                width="100%",
            ),
            rx.flex(
                rx.box(
                    rx.text(row["name"], font_weight="750", size="3"),
                    rx.box(
                        status_badge(row["is_active"], "Ativa", "Inativa"),
                        margin_top="0.45rem",
                    ),
                ),
                rx.flex(
                    rx.button(
                        "Editar",
                        type="button",
                        variant="outline",
                        color_scheme="teal",
                        on_click=AdminDirectoryState.begin_specialty_edit(
                            row["id"], row["name"]
                        ),
                        disabled=AdminDirectoryState.is_submitting,
                    ),
                    rx.button(
                        rx.cond(row["is_active"], "Desativar", "Reativar"),
                        type="button",
                        variant="ghost",
                        color_scheme=rx.cond(row["is_active"], "gray", "teal"),
                        on_click=AdminDirectoryState.toggle_specialty_active(
                            row["id"], row["is_active"]
                        ),
                        disabled=AdminDirectoryState.is_submitting,
                    ),
                    gap="0.5rem",
                    direction=rx.breakpoints(initial="column", sm="row"),
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                justify="between",
                align=rx.breakpoints(initial="stretch", sm="center"),
                gap="0.75rem",
                width="100%",
            ),
        ),
        width="100%",
        padding="0.95rem 1rem",
        border="1px solid var(--vitta-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-surface)",
        role="listitem",
    )


def specialties_list_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.heading("Especialidades cadastradas", size="4"),
                rx.text(
                    "Ativas e inativas",
                    size="1",
                    color="var(--vitta-text-muted)",
                ),
                justify="between",
                align="center",
                width="100%",
                gap="0.75rem",
            ),
            rx.cond(
                AdminDirectoryState.has_specialties,
                rx.vstack(
                    rx.foreach(AdminDirectoryState.specialties, specialty_row),
                    spacing="3",
                    width="100%",
                    role="list",
                ),
                rx.center(
                    rx.vstack(
                        rx.heading("Nenhuma especialidade cadastrada", size="3"),
                        rx.text(
                            "Cadastre a primeira especialidade para começar a montar o diretório profissional.",
                            color="var(--vitta-text-muted)",
                            text_align="center",
                            size="2",
                            max_width="44ch",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    min_height="8rem",
                    width="100%",
                ),
            ),
            spacing="4",
            width="100%",
            align="stretch",
        )
    )


def specialty_option(option) -> rx.Component:
    return rx.cond(
        option["is_active"] | option["selected"],
        rx.box(
            rx.checkbox(
                option["name"],
                checked=option["selected"],
                on_change=lambda _checked: AdminDirectoryState.toggle_professional_specialty(
                    option["id"]
                ),
                disabled=AdminDirectoryState.is_submitting | option["locked"],
                color_scheme="teal",
                high_contrast=True,
                size="2",
            ),
            rx.cond(
                option["locked"],
                rx.text(
                    "Vínculo histórico com especialidade inativa; será preservado.",
                    size="1",
                    color="var(--vitta-text-muted)",
                    margin_top="0.25rem",
                ),
                rx.fragment(),
            ),
            width="100%",
            padding="0.65rem 0.75rem",
            border="1px solid var(--vitta-border)",
            border_radius="var(--vitta-radius-control)",
            background=rx.cond(
                option["locked"],
                "var(--vitta-surface-muted)",
                "var(--vitta-surface)",
            ),
        ),
        rx.fragment(),
    )


def medical_account_select() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(
            id="professional-medical-account",
            width="100%",
            class_name="vitta-select-trigger",
            aria_describedby="medical-account-help",
        ),
        rx.select.content(
            rx.select.item("Sem conta vinculada", value="__none__"),
            rx.foreach(
                AdminDirectoryState.medical_accounts,
                lambda account: rx.select.item(
                    account["email"],
                    value=account["value"],
                ),
            ),
            position="popper",
        ),
        value=AdminDirectoryState.selected_medical_user,
        on_change=AdminDirectoryState.update_medical_user,
        disabled=AdminDirectoryState.is_submitting,
        size="3",
    )


def professional_form_panel() -> rx.Component:
    form_fields = rx.vstack(
        rx.box(
            field_label("Nome do profissional", "professional-name"),
            rx.el.input(
                id="professional-name",
                name="name",
                type="text",
                value=AdminDirectoryState.professional_name,
                on_change=AdminDirectoryState.update_professional_name,
                required=True,
                max_length=160,
                auto_complete="name",
                class_name="vitta-input",
                margin_top="0.4rem",
            ),
            width="100%",
        ),
        rx.box(
            field_label("Identificador profissional", "professional-registration"),
            rx.el.input(
                id="professional-registration",
                name="registration_identifier",
                type="text",
                value=AdminDirectoryState.registration_identifier,
                on_change=AdminDirectoryState.update_registration_identifier,
                required=True,
                max_length=80,
                class_name="vitta-input",
                aria_describedby="professional-registration-help",
                margin_top="0.4rem",
            ),
            rx.text(
                "Ex.: registro interno ou identificação profissional. O sistema não presume CRM, conselho ou UF nesta etapa.",
                id="professional-registration-help",
                size="1",
                color="var(--vitta-text-muted)",
                margin_top="0.35rem",
                line_height="1.45",
            ),
            width="100%",
        ),
        rx.el.fieldset(
            rx.el.legend(
                "Especialidades",
                font_weight="650",
                font_size="0.9rem",
                color="var(--vitta-text)",
                margin_bottom="0.55rem",
            ),
            rx.vstack(
                rx.foreach(AdminDirectoryState.specialty_options, specialty_option),
                rx.text(
                    "Selecione ao menos uma especialidade ativa. Vínculos históricos inativos permanecem bloqueados e preservados.",
                    size="1",
                    color="var(--vitta-text-muted)",
                    line_height="1.45",
                ),
                spacing="2",
                align="stretch",
                width="100%",
            ),
            width="100%",
            border="0",
            padding="0",
            margin="0",
        ),
        rx.box(
            field_label("Conta Médica opcional", "professional-medical-account"),
            rx.box(medical_account_select(), margin_top="0.4rem"),
            rx.text(
                "Somente contas locais com role Médico e ainda disponíveis podem ser vinculadas.",
                id="medical-account-help",
                size="1",
                color="var(--vitta-text-muted)",
                margin_top="0.35rem",
                line_height="1.45",
            ),
            width="100%",
        ),
        rx.button(
            rx.cond(
                AdminDirectoryState.is_editing_professional,
                "Salvar alterações",
                "Cadastrar profissional",
            ),
            type="submit",
            min_height="3rem",
            width=rx.breakpoints(initial="100%", sm="auto"),
            color_scheme="teal",
            high_contrast=True,
            disabled=AdminDirectoryState.is_submitting,
            loading=AdminDirectoryState.is_submitting,
        ),
        spacing="4",
        width="100%",
        align="stretch",
    )

    return section_panel(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.heading(AdminDirectoryState.professional_form_title, size="5"),
                    rx.text(
                        "O identificador profissional é genérico nesta fase; agenda e disponibilidade serão definidos em uma change posterior.",
                        color="var(--vitta-text-muted)",
                        size="2",
                        line_height="1.55",
                        margin_top="0.35rem",
                        max_width="62ch",
                    ),
                ),
                rx.cond(
                    AdminDirectoryState.is_editing_professional,
                    rx.button(
                        "Cancelar edição",
                        type="button",
                        variant="ghost",
                        on_click=AdminDirectoryState.cancel_professional_edit,
                        disabled=AdminDirectoryState.is_submitting,
                    ),
                    rx.fragment(),
                ),
                justify="between",
                align=rx.breakpoints(initial="stretch", sm="start"),
                direction=rx.breakpoints(initial="column", sm="row"),
                gap="0.75rem",
                width="100%",
            ),
            rx.el.form(
                form_fields,
                on_submit=AdminDirectoryState.save_professional,
                width="100%",
            ),
            spacing="4",
            width="100%",
            align="stretch",
        )
    )

def professional_row(row) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.text(row["name"], font_weight="760", size="3"),
                    rx.text(
                        row["registration_identifier"],
                        size="1",
                        color="var(--vitta-text-muted)",
                        margin_top="0.15rem",
                    ),
                ),
                status_badge(row["is_active"], "Ativo", "Inativo"),
                justify="between",
                align="start",
                gap="0.75rem",
                width="100%",
            ),
            rx.box(
                rx.text(
                    "Especialidades",
                    size="1",
                    font_weight="700",
                    color="var(--vitta-text-muted)",
                ),
                rx.text(
                    row["specialty_names"],
                    size="2",
                    line_height="1.5",
                    margin_top="0.2rem",
                ),
                width="100%",
            ),
            rx.cond(
                row["has_inactive_specialty"],
                rx.text(
                    "Este profissional possui ao menos um vínculo histórico com especialidade inativa.",
                    size="1",
                    color="var(--vitta-text-muted)",
                    line_height="1.45",
                ),
                rx.fragment(),
            ),
            rx.box(
                rx.text(
                    "Conta de acesso",
                    size="1",
                    font_weight="700",
                    color="var(--vitta-text-muted)",
                ),
                rx.text(row["user_email"], size="2", margin_top="0.2rem"),
                width="100%",
            ),
            rx.flex(
                rx.button(
                    "Editar",
                    type="button",
                    variant="outline",
                    color_scheme="teal",
                    on_click=AdminDirectoryState.begin_professional_edit(
                        row["id"],
                        row["name"],
                        row["registration_identifier"],
                        row["user_id"],
                        row["specialty_ids"],
                    ),
                    disabled=AdminDirectoryState.is_submitting,
                ),
                rx.button(
                    rx.cond(row["is_active"], "Desativar", "Reativar"),
                    type="button",
                    variant="ghost",
                    color_scheme=rx.cond(row["is_active"], "gray", "teal"),
                    on_click=AdminDirectoryState.toggle_professional_active(
                        row["id"], row["is_active"]
                    ),
                    disabled=AdminDirectoryState.is_submitting,
                ),
                gap="0.5rem",
                direction=rx.breakpoints(initial="column", sm="row"),
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        width="100%",
        padding="1rem",
        border="1px solid var(--vitta-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-surface)",
        role="listitem",
    )


def professionals_list_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.heading("Diretório de profissionais", size="5"),
                    rx.text(
                        "Profissionais inativos permanecem no histórico e podem ser reativados.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        margin_top="0.3rem",
                    ),
                ),
                rx.button(
                    "Novo profissional",
                    type="button",
                    variant="outline",
                    color_scheme="teal",
                    on_click=AdminDirectoryState.start_new_professional,
                    disabled=AdminDirectoryState.is_submitting,
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                align=rx.breakpoints(initial="stretch", sm="center"),
                justify="between",
                gap="0.75rem",
                width="100%",
            ),
            rx.cond(
                AdminDirectoryState.has_professionals,
                rx.vstack(
                    rx.foreach(AdminDirectoryState.professionals, professional_row),
                    spacing="3",
                    width="100%",
                    role="list",
                ),
                rx.center(
                    rx.vstack(
                        rx.heading("Nenhum profissional cadastrado", size="4"),
                        rx.text(
                            "Cadastre uma especialidade e depois o primeiro profissional da clínica.",
                            size="2",
                            color="var(--vitta-text-muted)",
                            text_align="center",
                            max_width="44ch",
                        ),
                        rx.button(
                            "Cadastrar primeiro profissional",
                            type="button",
                            color_scheme="teal",
                            high_contrast=True,
                            on_click=AdminDirectoryState.start_new_professional,
                            disabled=AdminDirectoryState.is_submitting,
                        ),
                        spacing="3",
                        align="center",
                    ),
                    min_height="10rem",
                    width="100%",
                ),
            ),
            spacing="4",
            width="100%",
            align="stretch",
        )
    )


def admin_directory_workspace() -> rx.Component:
    """Compose the administrator directory without introducing global navigation."""
    return rx.vstack(
        rx.box(
            rx.heading(
                "Profissionais e especialidades",
                size="8",
                letter_spacing="-0.03em",
            ),
            rx.text(
                "Mantenha o diretório que servirá de base para agenda e consultas. Esta área não cria contas, horários ou agendamentos.",
                color="var(--vitta-text-muted)",
                max_width="70ch",
                line_height="1.65",
                margin_top="0.45rem",
            ),
            width="100%",
        ),
        feedback_region(
            AdminDirectoryState.error_message,
            AdminDirectoryState.success_message,
            "admin-feedback",
        ),
        rx.cond(
            AdminDirectoryState.is_loading,
            rx.center(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text(
                        "Carregando diretório…",
                        size="2",
                        color="var(--vitta-text-muted)",
                    ),
                    spacing="2",
                    align="center",
                ),
                min_height="14rem",
                width="100%",
                role="status",
                aria_live="polite",
            ),
            rx.vstack(
                rx.flex(
                    rx.vstack(
                        specialty_create_panel(),
                        specialties_list_panel(),
                        spacing="4",
                        width="100%",
                        align="stretch",
                    ),
                    professional_form_panel(),
                    direction=rx.breakpoints(initial="column", xl="row"),
                    gap="1rem",
                    align="start",
                    width="100%",
                ),
                professionals_list_panel(),
                spacing="4",
                width="100%",
                align="stretch",
            ),
        ),
        spacing="5",
        width="100%",
        align="stretch",
    )
