"""Formulário único de equipe, usando componentes e eventos Reflex existentes."""

import reflex as rx

from vitta_one.auth.staff_state import AdminStaffState
from vitta_one.professional_directory.state import AdminDirectoryState
from vitta_one.ui.admin_directory_components import specialty_option
from vitta_one.ui.components import error_banner, field_label, section_panel


def _field_error(message, element_id: str) -> rx.Component:
    return rx.cond(
        message != "",
        rx.text(
            message, id=element_id, role="alert", aria_live="polite",
            color="var(--vitta-danger)", size="2", margin_top="0.35rem",
        ),
        rx.fragment(),
    )


def _identity_fields() -> rx.Component:
    return rx.vstack(
        rx.box(
            field_label("Nome completo *", "staff-create-name"),
            rx.el.input(
                id="staff-create-name", name="name", type="text",
                required=True, min_length=2, max_length=160,
                auto_complete="name", placeholder="Nome e sobrenome",
                value=AdminStaffState.new_name,
                on_change=AdminStaffState.update_new_name,
                class_name="vitta-input", margin_top="0.45rem",
                aria_invalid=AdminStaffState.name_error != "",
                aria_describedby=rx.cond(
                    AdminStaffState.name_error != "", "staff-name-error", "",
                ),
            ),
            _field_error(AdminStaffState.name_error, "staff-name-error"),
            width="100%", min_width="0",
        ),
        rx.box(
            field_label("E-mail de acesso *", "staff-create-email"),
            rx.el.input(
                id="staff-create-email", name="email", type="email",
                required=True, max_length=320,
                auto_complete="email", input_mode="email",
                placeholder="nome@clinica.com",
                value=AdminStaffState.new_email,
                on_change=AdminStaffState.update_new_email,
                class_name="vitta-input", margin_top="0.45rem",
                aria_invalid=AdminStaffState.email_error != "",
                aria_describedby=rx.cond(
                    AdminStaffState.email_error != "", "staff-email-error", "",
                ),
            ),
            _field_error(AdminStaffState.email_error, "staff-email-error"),
            width="100%", min_width="0",
        ),
        spacing="4", width="100%", align="stretch",
    )


def _password_field(*, qa: bool) -> rx.Component:
    field_id = "staff-medical-qa-password" if qa else "staff-reception-password"
    input_name = "qa_password" if qa else "password"
    label = "Senha de QA *" if qa else "Senha inicial *"
    help_text = (
        "Somente QA local: senha entre 12 e 128 caracteres, sem envio por e-mail."
        if qa else
        "Defina de 12 a 128 caracteres. Compartilhe a senha por um canal seguro."
    )
    return rx.box(
        field_label(label, field_id),
        rx.box(
            rx.el.input(
                id=field_id, name=input_name,
                type=rx.cond(AdminStaffState.show_password, "text", "password"),
                required=True,
                min_length=12, max_length=128, auto_complete="new-password",
                class_name="vitta-input vitta-password-input",
                placeholder="Digite a senha inicial",
                aria_invalid=AdminStaffState.password_error != "",
                aria_describedby=rx.cond(
                    AdminStaffState.password_error != "",
                    "staff-password-error staff-password-help",
                    "staff-password-help",
                ),
            ),
            rx.button(
                rx.cond(
                    AdminStaffState.show_password,
                    rx.icon("eye_off", size=19),
                    rx.icon("eye", size=19),
                ),
                type="button", variant="ghost", size="2",
                class_name="vitta-staff-password-toggle",
                on_click=AdminStaffState.toggle_password_visibility,
                aria_label=rx.cond(
                    AdminStaffState.show_password, "Ocultar senha", "Mostrar senha",
                ),
                aria_pressed=AdminStaffState.show_password,
            ),
            position="relative", margin_top="0.45rem",
        ),
        rx.text(
            help_text, id="staff-password-help", size="2",
            color="var(--vitta-text-muted)", margin_top="0.35rem",
        ),
        _field_error(AdminStaffState.password_error, "staff-password-error"),
        width="100%",
    )


def _medical_fields() -> rx.Component:
    return rx.vstack(
        rx.heading("Dados profissionais", size="4"),
        rx.text(
            "O identificador interno do médico será gerado pelo sistema.",
            size="2", color="var(--vitta-text-muted)",
        ),
        rx.el.fieldset(
            rx.el.legend(
                "Especialidades (opcional)",
                font_weight="700", font_size="0.9rem",
                color="var(--vitta-text)", margin_bottom="0.6rem",
            ),
            rx.cond(
                AdminDirectoryState.specialty_options.length() > 0,
                rx.vstack(
                    rx.foreach(AdminDirectoryState.specialty_options, specialty_option),
                    spacing="2", align="stretch", width="100%",
                ),
                rx.text(
                    "Nenhuma especialidade ativa disponível. Você pode cadastrar o médico e associar especialidades depois.",
                    size="2", color="var(--vitta-text-muted)",
                ),
            ),
            rx.text(
                "Associe uma ou mais especialidades ao médico. Você também poderá fazer isso posteriormente.",
                size="2", color="var(--vitta-text-muted)",
                line_height="1.5", margin_top="0.65rem",
            ),
            width="100%", border="0", padding="0", margin="0",
        ),
        rx.cond(
            AdminDirectoryState.qa_local_enabled,
            _password_field(qa=True),
            rx.box(
                rx.text(
                    "Primeiro acesso: o sistema gera uma senha temporária. "
                    "O envio das instruções depende do Resend configurado; "
                    "a confirmação do provedor não garante a entrega.",
                    size="2", line_height="1.55", color="var(--vitta-text-muted)",
                ),
                width="100%",
            ),
        ),
        spacing="4", width="100%", align="stretch",
        class_name="vitta-staff-specific",
    )


def _reception_fields() -> rx.Component:
    return rx.vstack(
        rx.heading("Credencial inicial", size="4"),
        _password_field(qa=False),
        spacing="4", width="100%", align="stretch",
        class_name="vitta-staff-specific",
    )


def _profile_change_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Alterar perfil do funcionário?"),
            rx.dialog.description(
                "Nome e e-mail serão preservados. As credenciais digitadas e as "
                "especialidades selecionadas no perfil anterior serão descartadas.",
            ),
            rx.flex(
                rx.button(
                    "Continuar preenchendo", type="button", variant="outline",
                    on_click=AdminStaffState.dismiss_profile_change,
                ),
                rx.button(
                    "Alterar perfil", type="button", color_scheme="teal",
                    on_click=AdminStaffState.confirm_profile_change,
                ),
                gap="3", justify="end",
                direction=rx.breakpoints(initial="column-reverse", sm="row"),
                width="100%", margin_top="1.25rem",
            ),
            max_width="28rem", class_name="vitta-dialog-content",
        ),
        open=AdminStaffState.profile_change_dialog_open,
        on_open_change=AdminStaffState.set_profile_change_dialog_open,
    )


def _cancel_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Descartar alterações?"),
            rx.dialog.description(
                "Os dados não salvos serão perdidos. Nenhum funcionário será cadastrado.",
            ),
            rx.flex(
                rx.button(
                    "Continuar cadastro", type="button", variant="outline",
                    on_click=AdminStaffState.dismiss_cancel,
                ),
                rx.button(
                    "Descartar e voltar", type="button", color_scheme="red",
                    on_click=AdminStaffState.confirm_cancel,
                ),
                gap="3", justify="end",
                direction=rx.breakpoints(initial="column-reverse", sm="row"),
                width="100%", margin_top="1.25rem",
            ),
            max_width="28rem", class_name="vitta-dialog-content",
        ),
        open=AdminStaffState.cancel_dialog_open,
        on_open_change=AdminStaffState.set_cancel_dialog_open,
    )


def admin_staff_panel() -> rx.Component:
    """Entrada canônica; rotas legadas reutilizam este formulário."""
    return rx.box(
        section_panel(
            rx.el.form(
                rx.vstack(
                    rx.box(
                        rx.heading("Perfil do funcionário", size="4"),
                        rx.text(
                            "Selecione o perfil. Apenas dados necessários a esse acesso serão solicitados.",
                            size="2", color="var(--vitta-text-muted)",
                            margin_top="0.35rem",
                        ),
                        width="100%",
                    ),
                    rx.box(
                        field_label("Perfil de acesso *", "staff-create-role"),
                        rx.select.root(
                            rx.select.trigger(
                                id="staff-create-role", width="100%",
                                placeholder="Selecione um perfil",
                                class_name="vitta-select-trigger",
                                margin_top="0.45rem",
                                aria_invalid=AdminStaffState.profile_error != "",
                                aria_describedby=rx.cond(
                                    AdminStaffState.profile_error != "",
                                    "staff-role-error", "",
                                ),
                            ),
                            rx.select.content(
                                rx.select.item("Médico", value="medico"),
                                rx.select.item("Recepcionista", value="recepcionista"),
                                position="popper",
                            ),
                            value=AdminStaffState.creation_profile,
                            on_change=AdminStaffState.select_creation_profile,
                            disabled=AdminStaffState.saving,
                            size="3",
                        ),
                        _field_error(AdminStaffState.profile_error, "staff-role-error"),
                        width="100%",
                    ),
                    rx.separator(),
                    rx.heading("Identificação", size="4"),
                    _identity_fields(),
                    rx.cond(
                        AdminStaffState.creation_profile == "medico",
                        rx.cond(
                            AdminDirectoryState.is_loading,
                            rx.center(
                                rx.spinner(size="3"), role="status",
                                aria_label="Carregando especialidades",
                                min_height="6rem", width="100%",
                            ),
                            _medical_fields(),
                        ),
                        rx.cond(
                            AdminStaffState.creation_profile == "recepcionista",
                            _reception_fields(),
                            rx.text(
                                "Selecione um perfil para visualizar os campos específicos.",
                                color="var(--vitta-text-muted)", size="2",
                            ),
                        ),
                    ),
                    rx.cond(
                        AdminStaffState.error != "",
                        error_banner(AdminStaffState.error, "staff-create-error"),
                        rx.fragment(),
                    ),
                    rx.flex(
                        rx.button(
                            "Cancelar", type="button", variant="outline",
                            on_click=AdminStaffState.request_cancel,
                            disabled=AdminStaffState.saving,
                        ),
                        rx.button(
                            rx.cond(
                                AdminStaffState.creation_profile == "medico",
                                "Cadastrar médico",
                                rx.cond(
                                    AdminStaffState.creation_profile == "recepcionista",
                                    "Cadastrar recepcionista", "Cadastrar funcionário",
                                ),
                            ),
                            type="submit", color_scheme="teal", high_contrast=True,
                            loading=AdminStaffState.saving,
                            disabled=AdminStaffState.saving | AdminDirectoryState.is_loading,
                        ),
                        gap="3", justify="end", align="center",
                        direction=rx.breakpoints(initial="column-reverse", sm="row"),
                        width="100%", class_name="vitta-staff-actions",
                    ),
                    spacing="4", width="100%", align="stretch",
                    class_name="vitta-form-panel",
                ),
                on_submit=AdminStaffState.create,
                no_validate=True, width="100%",
            ),
            padding=rx.breakpoints(initial="1rem", sm="1.4rem"),
        ),
        _profile_change_dialog(),
        _cancel_dialog(),
        width="100%", max_width="46rem", margin="0 auto",
        class_name="vitta-staff-form",
    )
