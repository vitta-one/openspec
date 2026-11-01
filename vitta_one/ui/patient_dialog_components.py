"""Focused patient identity and portal dialogs. Existing Reflex services own mutations."""

import reflex as rx

from vitta_one.patient_queue.state import ReceptionQueueState as S
from vitta_one.ui.components import field_label


def _close_control() -> rx.Component:
    return rx.dialog.close(
        rx.button(
            rx.icon("x", size=18),
            type="button",
            variant="ghost",
            color_scheme="gray",
            aria_label="Fechar janela",
        )
    )


def _dialog_header(title: str, description: str) -> rx.Component:
    return rx.flex(
        rx.box(
            rx.dialog.title(title, font_weight="750", color="var(--vitta-text)"),
            rx.dialog.description(
                description,
                size="2",
                color="var(--vitta-text-muted)",
                margin_top="0.35rem",
            ),
            min_width="0",
        ),
        _close_control(),
        justify="between",
        align="start",
        gap="3",
        width="100%",
    )


def _field_error(message, control_id: str) -> rx.Component:
    return rx.cond(
        message != "",
        rx.text(
            message,
            id=control_id,
            role="alert",
            color="var(--vitta-danger)",
            size="2",
            margin_top="0.35rem",
        ),
        rx.fragment(),
    )


def patient_edit_dialog() -> rx.Component:
    """Edit only the allowed patient fields; preserve the profile until commit."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                _dialog_header(
                    "Editar cadastro",
                    "Atualize as informações cadastrais do paciente.",
                ),
                rx.el.form(
                    rx.vstack(
                        rx.box(
                            field_label("Nome completo *", "patient-edit-name"),
                            rx.el.input(
                                id="patient-edit-name",
                                name="name",
                                type="text",
                                value=S.edit_patient_name,
                                on_change=S.update_edit_patient_name,
                                required=True,
                                max_length=160,
                                auto_complete="name",
                                auto_focus=True,
                                aria_describedby="patient-edit-name-error",
                                aria_invalid=S.edit_patient_name_error != "",
                                class_name="vitta-input",
                                margin_top="0.45rem",
                            ),
                            _field_error(S.edit_patient_name_error, "patient-edit-name-error"),
                            width="100%",
                        ),
                        rx.box(
                            field_label("Telefone (opcional)", "patient-edit-phone"),
                            rx.el.input(
                                id="patient-edit-phone",
                                name="phone",
                                type="tel",
                                input_mode="tel",
                                value=S.edit_patient_phone,
                                on_change=S.update_edit_patient_phone,
                                max_length=20,
                                auto_complete="tel-national",
                                placeholder="(11) 99999-9999",
                                aria_describedby="patient-edit-phone-error",
                                aria_invalid=S.edit_patient_phone_error != "",
                                class_name="vitta-input",
                                margin_top="0.45rem",
                            ),
                            _field_error(S.edit_patient_phone_error, "patient-edit-phone-error"),
                            width="100%",
                        ),
                        _field_error(S.edit_patient_form_error, "patient-edit-form-error"),
                        rx.flex(
                            rx.button(
                                "Cancelar",
                                type="button",
                                variant="outline",
                                color_scheme="gray",
                                on_click=S.change_patient_edit_dialog(False),
                                disabled=S.is_submitting,
                            ),
                            rx.button(
                                "Salvar alterações",
                                type="submit",
                                color_scheme="teal",
                                high_contrast=True,
                                loading=S.is_submitting,
                                disabled=S.is_submitting,
                            ),
                            justify="end",
                            align="center",
                            gap="3",
                            flex_wrap="wrap",
                            width="100%",
                            margin_top="0.4rem",
                        ),
                        spacing="4",
                        align="stretch",
                        width="100%",
                    ),
                    on_submit=S.update_selected_patient,
                    width="100%",
                    no_validate=True,
                ),
                spacing="5",
                align="stretch",
                width="100%",
            ),
            width="calc(100vw - 1.5rem)",
            max_width="30rem",
            max_height="calc(100dvh - 1.5rem)",
            overflow_y="auto",
            padding="1.5rem",
        ),
        open=S.edit_patient_dialog_open,
        on_open_change=S.change_patient_edit_dialog,
    )


def patient_portal_dialog() -> rx.Component:
    """Display persisted portal state and use the existing consented invitation flow."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                _dialog_header(
                    "Acesso ao portal",
                    "Consulte a situação da conta e gerencie o primeiro acesso.",
                ),
                rx.cond(
                    S.portal_dialog_loading,
                    rx.center(rx.spinner(size="3"), min_height="8rem", width="100%"),
                    rx.vstack(
                        rx.box(
                            rx.text("Paciente", size="2", color="var(--vitta-text-muted)"),
                            rx.text(
                                S.selected_patient_name,
                                font_weight="700",
                                color="var(--vitta-text)",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.box(
                            rx.text("Situação do acesso", size="2", color="var(--vitta-text-muted)"),
                            rx.text(
                                S.selected_patient_portal_status,
                                role="status",
                                aria_live="polite",
                                font_weight="650",
                                color="var(--vitta-primary)",
                                margin_top="0.3rem",
                            ),
                            width="100%",
                        ),
                        rx.cond(
                            S.portal_access_email != "",
                            rx.box(
                                rx.text("E-mail associado", size="2", color="var(--vitta-text-muted)"),
                                rx.text(S.portal_access_email, overflow_wrap="anywhere", font_weight="550"),
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        rx.separator(),
                        _field_error(S.portal_invitation_error, "patient-portal-invite-error"),
                        rx.cond(
                            S.portal_access_state == "ATIVO",
                            rx.text(
                                "Esta conta já possui acesso. Não é necessário enviar outro convite.",
                                size="2",
                                color="var(--vitta-text-muted)",
                            ),
                            rx.el.form(
                                rx.vstack(
                                    rx.box(
                                        field_label("E-mail para login *", "patient-portal-email"),
                                        rx.el.input(
                                            id="patient-portal-email",
                                            name="email",
                                            type="email",
                                            auto_complete="email",
                                            required=True,
                                            max_length=320,
                                            placeholder="paciente@exemplo.com",
                                            class_name="vitta-input",
                                            margin_top="0.45rem",
                                            aria_describedby="patient-portal-invite-error",
                                        ),
                                        width="100%",
                                    ),
                                    rx.el.label(
                                        rx.flex(
                                            rx.el.input(
                                                id="patient-portal-consent",
                                                name="consent_confirmed",
                                                type="checkbox",
                                                value="true",
                                                required=True,
                                                flex_shrink="0",
                                                margin_top="0.18rem",
                                                accent_color="var(--vitta-primary)",
                                            ),
                                            rx.text(
                                                "Confirmo que o paciente consentiu em receber o convite de ativação.",
                                                size="2",
                                                line_height="1.5",
                                            ),
                                            align="start",
                                            gap="3",
                                            width="100%",
                                        ),
                                        html_for="patient-portal-consent",
                                        display="block",
                                        cursor="pointer",
                                    ),
                                    rx.flex(
                                        rx.dialog.close(
                                            rx.button(
                                                "Fechar",
                                                type="button",
                                                variant="outline",
                                                color_scheme="gray",
                                            )
                                        ),
                                        rx.button(
                                            rx.cond(
                                                S.portal_access_state == "CONVITE_ENVIADO",
                                                "Reenviar convite",
                                                "Enviar convite de ativação",
                                            ),
                                            type="submit",
                                            color_scheme="teal",
                                            high_contrast=True,
                                            disabled=S.is_submitting,
                                            loading=S.is_submitting,
                                        ),
                                        justify="end",
                                        align="center",
                                        gap="3",
                                        flex_wrap="wrap",
                                        width="100%",
                                    ),
                                    spacing="4",
                                    align="stretch",
                                    width="100%",
                                ),
                                on_submit=S.issue_patient_portal_invitation,
                                no_validate=True,
                                width="100%",
                            ),
                        ),
                        spacing="3",
                        width="100%",
                        align="stretch",
                    ),
                ),
                spacing="4",
                width="100%",
                align="stretch",
            ),
            width="calc(100vw - 1.5rem)",
            max_width="32rem",
            max_height="calc(100dvh - 1.5rem)",
            overflow_y="auto",
            padding="1.5rem",
        ),
        open=S.portal_dialog_open,
        on_open_change=S.change_patient_portal_dialog,
    )
