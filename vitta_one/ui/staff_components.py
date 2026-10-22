"""Focused receptionist access form; directory lives on the employee list."""
import reflex as rx
from vitta_one.auth.staff_state import AdminStaffState
from vitta_one.ui.components import section_panel, field_label


def admin_staff_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.heading("Dados de acesso da Recepção", size="4"),
            rx.text(
                "Cadastre o e-mail institucional e defina uma senha inicial. "
                "A conta será exibida na lista de funcionários.",
                size="2", color="var(--vitta-text-muted)", line_height="1.6",
            ),
            rx.el.form(
                rx.vstack(
                    rx.box(
                        field_label("E-mail do recepcionista", "staff-email"),
                        rx.el.input(id="staff-email", name="email", type="email",
                                    required=True, max_length=320, auto_complete="off",
                                    class_name="vitta-input", margin_top="0.55rem",
                                    placeholder="recepcao@clinica.com"),
                        width="100%",
                    ),
                    rx.box(
                        field_label("Senha inicial (mínimo de 12 caracteres)", "staff-password"),
                        rx.el.input(id="staff-password", name="password", type="password",
                                    required=True, min_length=12, max_length=128,
                                    auto_complete="new-password",
                                    class_name="vitta-input", margin_top="0.55rem"),
                        rx.text("O funcionário poderá entrar com esse e-mail e senha.",
                                size="2", color="var(--vitta-text-muted)", margin_top="0.5rem"),
                        width="100%",
                    ),
                    rx.flex(
                        rx.link("Cancelar", href="/admin/funcionarios", class_name="vitta-context-link"),
                        rx.button("Cadastrar recepcionista", type="submit", color_scheme="teal",
                                  high_contrast=True, disabled=AdminStaffState.saving,
                                  loading=AdminStaffState.saving, min_height="2.85rem"),
                        align="center", justify="end", gap="3", width="100%", flex_wrap="wrap",
                    ),
                    spacing="5", align="stretch", width="100%",
                ),
                on_submit=AdminStaffState.create, width="100%",
            ),
            spacing="5", align="stretch", width="100%",
            class_name="vitta-form-panel",
        )
    )
