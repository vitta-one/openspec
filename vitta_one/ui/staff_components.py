"""Receptionist creation surface scoped to the Administrator dashboard."""
import reflex as rx
from vitta_one.auth.staff_state import AdminStaffState
from vitta_one.ui.components import section_panel, field_label, feedback_region

def admin_staff_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.heading("Acessos da Recepção", size="5"),
            rx.text("Cadastre um recepcionista. Médicos são cadastrados em Novo profissional.",
                    color="var(--vitta-text-muted)"),
            feedback_region(AdminStaffState.error, AdminStaffState.success, "staff-feedback"),
            rx.el.form(
                rx.grid(
                    rx.box(
                        field_label("E-mail", "staff-email"),
                        rx.el.input(id="staff-email", name="email", type="email",
                                    required=True, max_length=320, auto_complete="off",
                                    class_name="vitta-input", margin_top="0.4rem",
                                    placeholder="recepcao@clinica.com"),
                    ),
                    rx.box(
                        field_label("Senha inicial (12 caracteres ou mais)", "staff-password"),
                        rx.el.input(id="staff-password", name="password", type="password",
                                    required=True, min_length=12, max_length=128,
                                    auto_complete="new-password",
                                    class_name="vitta-input", margin_top="0.4rem"),
                    ),
                    columns=rx.breakpoints(initial="1", md="2"), gap="1rem", width="100%",
                ),
                rx.button("Cadastrar recepcionista", type="submit", color_scheme="teal",
                          high_contrast=True, disabled=AdminStaffState.saving,
                          loading=AdminStaffState.saving, margin_top="1rem"),
                on_submit=AdminStaffState.create, width="100%",
            ),
            rx.heading("Recepcionistas cadastrados", size="3"),
            rx.cond(AdminStaffState.emails.length() > 0,
                    rx.vstack(rx.foreach(AdminStaffState.emails,
                                         lambda email: rx.text(email, color="var(--vitta-text)")),
                              align="start", width="100%"),
                    rx.text("Nenhum recepcionista cadastrado.", color="var(--vitta-text-muted)")),
            spacing="4", align="stretch", width="100%",
        )
    )
