"""Role-specific agenda and operational workspace components."""

import reflex as rx

from vitta_one.doctor_workspace.state import DoctorWorkspaceState
from vitta_one.patient_portal.state import AdminClinicConfigurationState, PatientPortalState
from vitta_one.ui.components import empty_state, section_panel

_WEEKDAYS = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")


def _calendar_grid(cells, month_label, previous, next_) -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.button("‹", type="button", variant="outline", aria_label="Mês anterior", on_click=previous),
                rx.heading(month_label, size="4", text_align="center"),
                rx.button("›", type="button", variant="outline", aria_label="Próximo mês", on_click=next_),
                justify="between",
                align="center",
                width="100%",
            ),
            rx.grid(
                *[rx.text(day, size="1", text_align="center", color="var(--vitta-text-muted)") for day in _WEEKDAYS],
                columns="repeat(7, minmax(0, 1fr))",
                gap="1",
                width="100%",
            ),
            rx.grid(
                rx.foreach(
                    cells,
                    lambda cell: rx.box(
                        rx.text(cell["day"], size="2", font_weight="700"),
                        rx.cond(
                            cell["count"] > 0,
                            rx.badge(cell["count"], color_scheme="teal", variant="soft", size="1"),
                            rx.fragment(),
                        ),
                        min_height="3.1rem",
                        padding="0.45rem",
                        border="1px solid var(--vitta-border)",
                        border_radius="0.65rem",
                        background=rx.cond(cell["count"] > 0, "var(--vitta-primary-soft)", "var(--vitta-surface)"),
                        overflow="hidden",
                    ),
                ),
                columns="repeat(7, minmax(0, 1fr))",
                gap="1",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        )
    )


def _doctor_week_day(day) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(day["day_label"], size="2", font_weight="700",
                    color="var(--vitta-text-muted)"),
            rx.heading(day["date_label"], size="5"),
            rx.separator(),
            rx.cond(
                day["entries"].length() > 0,
                rx.vstack(
                    rx.foreach(day["entries"], lambda event:
                        rx.box(
                            rx.text(event["time"], font_weight="750",
                                    color="#115e59", size="2"),
                            rx.text(event["patient_name"], font_weight="650", size="2"),
                            rx.text(event["status"], color="var(--vitta-text-muted)",
                                    size="1"),
                            class_name="vitta-agenda-event",
                        )
                    ),
                    spacing="2", width="100%", align="stretch",
                ),
                rx.text("Sem consultas", size="1",
                        color="var(--vitta-text-muted)", padding_top="0.75rem"),
            ),
            spacing="3", width="100%", align="stretch",
        ),
        class_name="vitta-agenda-day",
    )


def doctor_week_calendar() -> rx.Component:
    """Reuse the seven-lane calendar visual language from Reception."""
    return section_panel(
        rx.vstack(
            rx.heading("Minha semana", size="5"),
            rx.text("Próximos sete dias de consultas sob sua responsabilidade.",
                    size="2", color="var(--vitta-text-muted)"),
            rx.box(
                rx.grid(
                    rx.foreach(DoctorWorkspaceState.calendar_week, _doctor_week_day),
                    columns="7", gap="2", class_name="vitta-agenda-week-grid",
                ),
                width="100%", overflow_x="auto", class_name="vitta-agenda-week-scroll",
            ),
            spacing="4", align="stretch", width="100%",
        ),
    )


def doctor_calendar() -> rx.Component:
    return _calendar_grid(
        DoctorWorkspaceState.calendar_cells,
        DoctorWorkspaceState.month_label,
        DoctorWorkspaceState.previous_month,
        DoctorWorkspaceState.next_month,
    )


def patient_calendar() -> rx.Component:
    return _calendar_grid(
        PatientPortalState.calendar_cells,
        PatientPortalState.month_label,
        PatientPortalState.previous_month,
        PatientPortalState.next_month,
    )


def doctor_consultation_list() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.heading("Consultas do período", size="4"),
            rx.cond(
                DoctorWorkspaceState.is_loading,
                rx.center(rx.spinner(size="3"), min_height="8rem", role="status", aria_live="polite"),
                rx.cond(
                    DoctorWorkspaceState.has_consultations,
                    rx.vstack(
                        rx.foreach(
                            DoctorWorkspaceState.consultation_rows,
                            lambda row: rx.box(
                                rx.flex(
                                    rx.vstack(
                                        rx.text(row["scheduled_at"], font_weight="750", class_name="vitta-tabular"),
                                        rx.text(row["patient_name"], color="var(--vitta-text-muted)"),
                                        spacing="1",
                                        align="start",
                                    ),
                                    rx.badge(row["status"], color_scheme="teal", variant="soft"),
                                    justify="between",
                                    align="start",
                                    gap="2",
                                    width="100%",
                                    flex_wrap="wrap",
                                ),
                                rx.text(row["specialty"], size="2", color="var(--vitta-text-muted)", margin_top="0.4rem"),
                                rx.cond(
                                    row["rescheduled_from"] != "",
                                    rx.text("Reagendada. Data anterior: ", row["rescheduled_from"], size="1", color="var(--vitta-text-subtle)", margin_top="0.35rem"),
                                    rx.fragment(),
                                ),
                                padding="0.9rem",
                                border="1px solid var(--vitta-border)",
                                border_radius="0.8rem",
                                width="100%",
                                role="listitem",
                            ),
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    empty_state("calendar", "Nenhuma consulta neste período", "Use as setas para consultar outros meses."),
                ),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        )
    )


def doctor_patient_list() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.heading("Pacientes vinculados às suas consultas", size="4"),
            rx.text(
                "Esta lista inclui somente pessoas com consulta associada ao seu cadastro profissional.",
                size="2",
                color="var(--vitta-text-muted)",
            ),
            rx.cond(
                DoctorWorkspaceState.is_loading,
                rx.center(rx.spinner(size="3"), min_height="8rem", role="status", aria_live="polite"),
                rx.cond(
                    DoctorWorkspaceState.has_patients,
                    rx.vstack(
                        rx.foreach(
                            DoctorWorkspaceState.patient_rows,
                            lambda row: rx.flex(
                                rx.text(row["name"], font_weight="700"),
                                rx.text("Consulta: ", row["recent_consultation"], size="2", color="var(--vitta-text-muted)"),
                                justify="between",
                                align="center",
                                gap="2",
                                flex_wrap="wrap",
                                padding="0.85rem",
                                border="1px solid var(--vitta-border)",
                                border_radius="0.75rem",
                                width="100%",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    empty_state("users", "Ainda não há pacientes vinculados", "Pacientes aparecem após serem associados a uma consulta sua."),
                ),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        )
    )


def patient_consultation_list() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.heading("Minhas consultas", size="4"),
            rx.cond(
                PatientPortalState.is_loading,
                rx.center(rx.spinner(size="3"), min_height="8rem", role="status", aria_live="polite"),
                rx.cond(
                    PatientPortalState.has_consultations,
                    rx.vstack(
                        rx.foreach(
                            PatientPortalState.consultation_rows,
                            lambda row: rx.box(
                                rx.flex(
                                    rx.vstack(
                                        rx.text(row["scheduled_at"], font_weight="750", class_name="vitta-tabular"),
                                        rx.text(row["professional_name"], color="var(--vitta-text-muted)"),
                                        spacing="1",
                                        align="start",
                                    ),
                                    rx.badge(row["status"], color_scheme=rx.cond(row["status"] == "Cancelada", "gray", "teal"), variant="soft"),
                                    justify="between",
                                    align="start",
                                    gap="2",
                                    flex_wrap="wrap",
                                    width="100%",
                                ),
                                rx.text(row["specialty"], size="2", color="var(--vitta-text-muted)", margin_top="0.5rem"),
                                rx.cond(
                                    row["rescheduled_from"] != "",
                                    rx.text("Esta consulta foi reagendada. Data anterior: ", row["rescheduled_from"], size="2", color="var(--vitta-text-subtle)", margin_top="0.45rem"),
                                    rx.fragment(),
                                ),
                                rx.cond(
                                    PatientPortalState.location_configured,
                                    rx.text(PatientPortalState.clinic_name, " · ", PatientPortalState.clinic_address, size="2", margin_top="0.55rem"),
                                    rx.text("Endereço ainda não configurado pela Administração.", size="2", color="var(--vitta-text-muted)", margin_top="0.55rem"),
                                ),
                                padding="1rem",
                                border="1px solid var(--vitta-border)",
                                border_radius="0.85rem",
                                width="100%",
                                role="listitem",
                            ),
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    empty_state("calendar", "Nenhuma consulta neste período", "Suas consultas futuras e passadas aparecem aqui conforme o mês selecionado."),
                ),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        )
    )


def patient_clinic_location() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.heading("Local de atendimento", size="4"),
            rx.cond(
                PatientPortalState.location_configured,
                rx.vstack(
                    rx.text(PatientPortalState.clinic_name, font_weight="750"),
                    rx.text(PatientPortalState.clinic_address, size="2", color="var(--vitta-text-muted)"),
                    spacing="1",
                    align="start",
                ),
                rx.text("Endereço ainda não configurado pela Administração.", size="2", color="var(--vitta-text-muted)"),
            ),
            spacing="2",
            width="100%",
            align="stretch",
        )
    )


def admin_clinic_configuration() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.heading("Local da clínica no portal", size="4"),
                rx.badge(
                    rx.cond(AdminClinicConfigurationState.configured, "Configurado", "Pendente"),
                    color_scheme=rx.cond(AdminClinicConfigurationState.configured, "green", "amber"),
                    variant="soft",
                ),
                justify="between",
                align="center",
                gap="2",
                flex_wrap="wrap",
                width="100%",
            ),
            rx.cond(
                AdminClinicConfigurationState.configured,
                rx.vstack(
                    rx.text(AdminClinicConfigurationState.clinic_name, font_weight="750"),
                    rx.text(AdminClinicConfigurationState.clinic_address, size="2", color="var(--vitta-text-muted)"),
                    spacing="1",
                    align="start",
                ),
                rx.text(
                    "Endereço ainda não configurado pela Administração. Defina VITTA_ONE_CLINIC_NAME e VITTA_ONE_CLINIC_ADDRESS no ambiente da implantação.",
                    size="2",
                    color="var(--vitta-text-muted)",
                    line_height="1.5",
                ),
            ),
            spacing="2",
            width="100%",
            align="stretch",
        )
    )
