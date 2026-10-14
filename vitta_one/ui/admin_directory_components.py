"""Reusable administrator UI for professional and specialty management."""

import reflex as rx

from vitta_one.professional_directory.state import AdminDirectoryState
from vitta_one.ui.components import (
    error_banner,
    feedback_region,
    field_label,
    page_header,
    section_panel,
)


def status_badge(is_active, active_label: str, inactive_label: str) -> rx.Component:
    """Show textual status with color only as a secondary cue."""
    return rx.cond(
        is_active,
        rx.badge(active_label, color_scheme="green", high_contrast=True, variant="soft"),
        rx.badge(inactive_label, color_scheme="gray", high_contrast=True, variant="soft"),
    )


def specialty_row(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["name"], font_weight="750", size="3"),
                rx.box(
                    status_badge(row["is_active"], "Ativa", "Inativa"),
                    margin_top="0.45rem",
                ),
                min_width="0",
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
                rx.box(
                    rx.heading("Especialidades", size="5"),
                    rx.text(
                        "Consulte as áreas da clínica. Uma especialidade desativada pode ser reativada.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        margin_top="0.3rem",
                        line_height="1.5",
                    ),
                ),
                rx.link(
                    "Ver todas",
                    href="/admin/especialidades",
                    class_name="vitta-text-link",
                    aria_label="Ver todas as especialidades",
                    white_space="nowrap",
                ),
                justify="between",
                align="start",
                width="100%",
                gap="0.75rem",
            ),
            rx.cond(
                AdminDirectoryState.has_recent_specialties,
                rx.vstack(
                    rx.foreach(AdminDirectoryState.recent_specialties, specialty_row),
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
                        rx.button(
                            "Nova especialidade",
                            type="button",
                            color_scheme="teal",
                            high_contrast=True,
                            on_click=AdminDirectoryState.start_new_specialty,
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


def _specialty_create_form() -> rx.Component:
    return rx.el.form(
        rx.vstack(
            rx.cond(
                AdminDirectoryState.error_message != "",
                error_banner(
                    AdminDirectoryState.error_message,
                    "specialty-dialog-error",
                ),
                rx.fragment(),
            ),
            rx.box(
                field_label("Nome da especialidade", "specialty-create-name"),
                rx.el.input(
                    id="specialty-create-name",
                    name="name",
                    type="text",
                    value=AdminDirectoryState.new_specialty_name,
                    on_change=AdminDirectoryState.update_new_specialty_name,
                    required=True,
                    max_length=120,
                    class_name="vitta-input",
                    aria_invalid=AdminDirectoryState.error_message != "",
                    aria_describedby=rx.cond(
                        AdminDirectoryState.error_message != "",
                        "specialty-dialog-error",
                        "",
                    ),
                    margin_top="0.4rem",
                    auto_focus=True,
                ),
                width="100%",
            ),
            rx.flex(
                rx.button(
                    "Cancelar",
                    type="button",
                    variant="ghost",
                    on_click=AdminDirectoryState.cancel_specialty_dialog,
                    disabled=AdminDirectoryState.is_submitting,
                ),
                rx.button(
                    "Cadastrar especialidade",
                    type="submit",
                    color_scheme="teal",
                    high_contrast=True,
                    disabled=AdminDirectoryState.is_submitting,
                    loading=AdminDirectoryState.is_submitting,
                ),
                justify="end",
                gap="0.5rem",
                direction=rx.breakpoints(initial="column-reverse", sm="row"),
                width="100%",
            ),
            spacing="4",
            align="stretch",
            width="100%",
        ),
        on_submit=AdminDirectoryState.create_specialty,
        no_validate=True,
        width="100%",
    )


def _specialty_edit_form() -> rx.Component:
    return rx.el.form(
        rx.vstack(
            rx.cond(
                AdminDirectoryState.error_message != "",
                error_banner(
                    AdminDirectoryState.error_message,
                    "specialty-dialog-error",
                ),
                rx.fragment(),
            ),
            rx.box(
                field_label("Nome da especialidade", "specialty-edit-name"),
                rx.el.input(
                    id="specialty-edit-name",
                    name="name",
                    type="text",
                    value=AdminDirectoryState.editing_specialty_name,
                    on_change=AdminDirectoryState.update_specialty_edit_name,
                    required=True,
                    max_length=120,
                    class_name="vitta-input",
                    aria_invalid=AdminDirectoryState.error_message != "",
                    aria_describedby=rx.cond(
                        AdminDirectoryState.error_message != "",
                        "specialty-dialog-error",
                        "",
                    ),
                    margin_top="0.4rem",
                    auto_focus=True,
                ),
                width="100%",
            ),
            rx.flex(
                rx.button(
                    "Cancelar",
                    type="button",
                    variant="ghost",
                    on_click=AdminDirectoryState.cancel_specialty_dialog,
                    disabled=AdminDirectoryState.is_submitting,
                ),
                rx.button(
                    "Salvar alterações",
                    type="submit",
                    color_scheme="teal",
                    high_contrast=True,
                    disabled=AdminDirectoryState.is_submitting,
                    loading=AdminDirectoryState.is_submitting,
                ),
                justify="end",
                gap="0.5rem",
                direction=rx.breakpoints(initial="column-reverse", sm="row"),
                width="100%",
            ),
            spacing="4",
            align="stretch",
            width="100%",
        ),
        on_submit=AdminDirectoryState.save_specialty_edit,
        no_validate=True,
        width="100%",
    )


def specialty_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    AdminDirectoryState.editing_specialty_id > 0,
                    "Editar especialidade",
                    "Nova especialidade",
                )
            ),
            rx.dialog.description(
                rx.cond(
                    AdminDirectoryState.editing_specialty_id > 0,
                    "Atualize o nome sem alterar os vínculos históricos existentes.",
                    "Cadastre uma área de atuação para usar no diretório de profissionais.",
                ),
                margin_top="0.35rem",
                margin_bottom="1rem",
            ),
            rx.cond(
                AdminDirectoryState.editing_specialty_id > 0,
                _specialty_edit_form(),
                _specialty_create_form(),
            ),
            class_name="vitta-dialog-content",
            max_width="34rem",
        ),
        open=AdminDirectoryState.specialty_dialog_open,
        on_open_change=AdminDirectoryState.set_specialty_dialog_open,
    )


def _professional_form_fields() -> rx.Component:
    return rx.vstack(
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
                auto_focus=True,
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
        spacing="4",
        width="100%",
        align="stretch",
    )


def professional_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(AdminDirectoryState.professional_form_title),
            rx.dialog.description(
                "Mantenha identificação, especialidades e vínculo opcional de acesso Médico. Agenda e disponibilidade continuam em capability própria.",
                margin_top="0.35rem",
                margin_bottom="1rem",
            ),
            rx.cond(
                AdminDirectoryState.error_message != "",
                error_banner(
                    AdminDirectoryState.error_message,
                    "professional-dialog-error",
                ),
                rx.fragment(),
            ),
            rx.el.form(
                rx.vstack(
                    _professional_form_fields(),
                    rx.flex(
                        rx.button(
                            "Cancelar",
                            type="button",
                            variant="ghost",
                            on_click=AdminDirectoryState.cancel_professional_dialog,
                            disabled=AdminDirectoryState.is_submitting,
                        ),
                        rx.button(
                            rx.cond(
                                AdminDirectoryState.is_editing_professional,
                                "Salvar alterações",
                                "Cadastrar profissional",
                            ),
                            type="submit",
                            color_scheme="teal",
                            high_contrast=True,
                            disabled=AdminDirectoryState.is_submitting,
                            loading=AdminDirectoryState.is_submitting,
                        ),
                        justify="end",
                        gap="0.5rem",
                        direction=rx.breakpoints(initial="column-reverse", sm="row"),
                        width="100%",
                    ),
                    spacing="4",
                    align="stretch",
                    width="100%",
                ),
                on_submit=AdminDirectoryState.save_professional,
                no_validate=True,
                width="100%",
            ),
            class_name="vitta-dialog-content vitta-dialog-content-wide",
            max_width="46rem",
        ),
        open=AdminDirectoryState.professional_dialog_open,
        on_open_change=AdminDirectoryState.set_professional_dialog_open,
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


def professional_summary_row(row) -> rx.Component:
    """Compact dashboard item; detailed fields remain on the complete page."""
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["name"], font_weight="700", size="3"),
                rx.text(
                    row["specialty_names"], size="2",
                    color="var(--vitta-text-muted)", margin_top="0.3rem",
                    overflow_wrap="anywhere",
                ),
                min_width="0",
            ),
            status_badge(row["is_active"], "Ativo", "Inativo"),
            justify="between", gap="1rem", width="100%", align="start",
        ),
        padding="1rem",
        border="1px solid var(--vitta-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-surface)",
        width="100%", role="listitem",
    )


def professionals_list_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.heading("Profissionais", size="5"),
                    rx.text(
                        "Equipe cadastrada na clínica.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        margin_top="0.3rem",
                    ),
                    min_width="0",
                ),
                rx.link(
                    "Ver todos",
                    href="/admin/profissionais",
                    class_name="vitta-text-link",
                    aria_label="Ver todos os profissionais",
                    white_space="nowrap",
                ),
                justify="between",
                gap="1rem",
                align="start",
                width="100%",
            ),
            rx.cond(
                AdminDirectoryState.has_recent_professionals,
                rx.vstack(
                    rx.foreach(AdminDirectoryState.recent_professionals, professional_summary_row),
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
    """Compose the premium administrator directory workspace."""
    return rx.vstack(
        page_header(
            "Administração",
            "Profissionais e especialidades",
            "Organize a equipe e as áreas de atendimento da clínica.",
            rx.button(
                rx.hstack(
                    rx.icon("plus", size=17),
                    rx.text("Nova especialidade"),
                    spacing="2",
                    align="center",
                ),
                type="button",
                variant="outline",
                color_scheme="teal",
                on_click=AdminDirectoryState.start_new_specialty,
                disabled=AdminDirectoryState.is_submitting,
            ),
            rx.button(
                rx.hstack(
                    rx.icon("user_plus", size=17),
                    rx.text("Novo profissional"),
                    spacing="2",
                    align="center",
                ),
                type="button",
                color_scheme="teal",
                high_contrast=True,
                on_click=AdminDirectoryState.start_new_professional,
                disabled=AdminDirectoryState.is_submitting,
            ),
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
            rx.grid(
                specialties_list_panel(),
                professionals_list_panel(),
                columns=rx.breakpoints(
                    initial="1",
                    xl="minmax(20rem, 0.8fr) minmax(0, 1.2fr)",
                ),
                gap="1rem",
                width="100%",
                align_items="start",
            ),
        ),
        specialty_dialog(),
        professional_dialog(),
        spacing="5",
        width="100%",
        align="stretch",
    )


def _directory_status_filter(*, is_professional: bool) -> rx.Component:
    """Shared accessible status filter for both complete admin directories."""
    control_id = "professional-status-filter" if is_professional else "specialty-status-filter"
    value = (
        AdminDirectoryState.professional_status
        if is_professional else AdminDirectoryState.specialty_status
    )
    update = (
        AdminDirectoryState.update_professional_status
        if is_professional else AdminDirectoryState.update_specialty_status
    )
    return rx.select.root(
        rx.select.trigger(id=control_id, width="100%", class_name="vitta-select-trigger"),
        rx.select.content(
            rx.select.item("Todas as situações", value="all"),
            rx.select.item("Ativas" if not is_professional else "Ativos", value="active"),
            rx.select.item("Inativas" if not is_professional else "Inativos", value="inactive"),
        ),
        value=value,
        on_change=update,
        size="3",
    )


def _directory_professional_specialty_filter() -> rx.Component:
    """Optional specialty filter backed by the loaded authorized directory."""
    return rx.select.root(
        rx.select.trigger(
            id="professional-specialty-filter", width="100%",
            class_name="vitta-select-trigger",
        ),
        rx.select.content(
            rx.select.item("Todas as especialidades", value="all"),
            rx.foreach(
                AdminDirectoryState.professional_specialty_filter_options,
                lambda option: rx.select.item(option["name"], value=option["value"]),
            ),
        ),
        value=AdminDirectoryState.professional_specialty_filter,
        on_change=AdminDirectoryState.update_professional_specialty_filter,
        size="3",
    )


def _directory_filters(*, is_professional: bool) -> rx.Component:
    """Search/filter region; inputs keep labels visible on narrow screens."""
    search_id = "professional-directory-search" if is_professional else "specialty-directory-search"
    value = (
        AdminDirectoryState.professional_search
        if is_professional else AdminDirectoryState.specialty_search
    )
    update = (
        AdminDirectoryState.update_professional_search
        if is_professional else AdminDirectoryState.update_specialty_search
    )
    return rx.grid(
        rx.box(
            field_label("Buscar profissional" if is_professional else "Buscar especialidade", search_id),
            rx.el.input(
                id=search_id, type="search", value=value, on_change=update,
                placeholder="Nome ou e-mail" if is_professional else "Nome da especialidade",
                class_name="vitta-input", margin_top="0.4rem",
                auto_complete="off",
            ),
        ),
        rx.box(
            field_label("Situação", "professional-status-filter" if is_professional else "specialty-status-filter"),
            rx.box(_directory_status_filter(is_professional=is_professional), margin_top="0.4rem"),
        ),
        *(
            [
                rx.box(
                    field_label("Especialidade", "professional-specialty-filter"),
                    rx.box(_directory_professional_specialty_filter(), margin_top="0.4rem"),
                )
            ]
            if is_professional else []
        ),
        columns=rx.breakpoints(initial="1", sm="repeat(2, minmax(0, 1fr))",
                               lg="repeat(3, minmax(0, 1fr))" if is_professional
                               else "repeat(2, minmax(0, 1fr))"),
        gap="1rem",
        width="100%",
    )


def _directory_pagination(*, is_professional: bool) -> rx.Component:
    page = (
        AdminDirectoryState.professional_page
        if is_professional else AdminDirectoryState.specialty_page
    )
    count = (
        AdminDirectoryState.professional_page_count
        if is_professional else AdminDirectoryState.specialty_page_count
    )
    move = (
        AdminDirectoryState.move_professional_page
        if is_professional else AdminDirectoryState.move_specialty_page
    )
    return rx.cond(
        count > 1,
        rx.flex(
            rx.button("Anterior", variant="outline", type="button",
                      disabled=page <= 1, on_click=move(-1)),
            rx.text("Página ", page, " de ", count, color="var(--vitta-text-muted)", size="2"),
            rx.button("Próxima", variant="outline", type="button",
                      disabled=page >= count, on_click=move(1)),
            align="center", justify="center", gap="1rem", flex_wrap="wrap",
            width="100%", margin_top="0.5rem",
        ),
        rx.fragment(),
    )


def specialties_management_workspace() -> rx.Component:
    """All specialties live on a dedicated authenticated management page."""
    return rx.vstack(
        page_header(
            "Administração", "Todas as especialidades",
            "Organize as áreas de atendimento cadastradas.",
            rx.button("Nova especialidade", type="button", color_scheme="teal",
                      on_click=AdminDirectoryState.start_new_specialty),
        ),
        rx.link("← Voltar ao painel", href="/admin", class_name="vitta-text-link"),
        feedback_region(AdminDirectoryState.error_message, AdminDirectoryState.success_message),
        section_panel(
            rx.vstack(
                _directory_filters(is_professional=False),
                rx.cond(
                    AdminDirectoryState.is_loading,
                    rx.center(rx.spinner(size="3"), min_height="8rem", width="100%"),
                    rx.cond(
                        AdminDirectoryState.has_filtered_specialties,
                        rx.vstack(
                            rx.foreach(AdminDirectoryState.paged_specialties, specialty_row),
                            spacing="3", align="stretch", width="100%", role="list",
                        ),
                        rx.center(
                            rx.text("Nenhuma especialidade encontrada. Ajuste a busca ou os filtros.",
                                    color="var(--vitta-text-muted)", text_align="center"),
                            min_height="8rem", width="100%",
                        ),
                    ),
                ),
                _directory_pagination(is_professional=False),
                spacing="4", align="stretch", width="100%",
            )
        ),
        specialty_dialog(),
        professional_dialog(),
        spacing="4", align="stretch", width="100%",
    )


def professionals_management_workspace() -> rx.Component:
    """All professionals live on a dedicated authenticated management page."""
    return rx.vstack(
        page_header(
            "Administração", "Todos os profissionais",
            "Encontre, cadastre e organize a equipe da clínica.",
            rx.button("Novo profissional", type="button", color_scheme="teal",
                      on_click=AdminDirectoryState.start_new_professional),
        ),
        rx.link("← Voltar ao painel", href="/admin", class_name="vitta-text-link"),
        feedback_region(AdminDirectoryState.error_message, AdminDirectoryState.success_message),
        section_panel(
            rx.vstack(
                _directory_filters(is_professional=True),
                rx.cond(
                    AdminDirectoryState.is_loading,
                    rx.center(rx.spinner(size="3"), min_height="8rem", width="100%"),
                    rx.cond(
                        AdminDirectoryState.has_filtered_professionals,
                        rx.vstack(
                            rx.foreach(AdminDirectoryState.paged_professionals, professional_row),
                            spacing="3", align="stretch", width="100%", role="list",
                        ),
                        rx.center(
                            rx.text("Nenhum profissional encontrado. Ajuste a busca ou os filtros.",
                                    color="var(--vitta-text-muted)", text_align="center"),
                            min_height="8rem", width="100%",
                        ),
                    ),
                ),
                _directory_pagination(is_professional=True),
                spacing="4", align="stretch", width="100%",
            )
        ),
        professional_dialog(),
        specialty_dialog(),
        spacing="4", align="stretch", width="100%",
    )
