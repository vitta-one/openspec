"""Role-specific agenda and operational workspace components."""

import reflex as rx

from vitta_one.doctor_workspace.state import DoctorWorkspaceState
from vitta_one.patient_portal.state import AdminClinicConfigurationState, PatientPortalState
from vitta_one.ui.components import empty_state, section_panel, field_label, feedback_region

_WEEKDAYS = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")


def _calendar_grid(
    cells, month_label, previous, next_, *, heading: str | None = None,
    class_name: str | None = None,
) -> rx.Component:
    children: list[rx.Component] = []
    if heading:
        children.extend(
            (
                rx.hstack(
                    rx.box(
                        rx.icon("calendar_days", size=28),
                        class_name="vitta-doctor-month-heading-icon",
                        aria_hidden="true",
                    ),
                    rx.heading(heading, size="5"),
                    align="center",
                    gap="4",
                    width="100%",
                    class_name="vitta-doctor-month-heading",
                ),
                rx.separator(),
            )
        )
    children.extend(
        (
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
                gap="0.25rem",
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
                gap="0.25rem",
                width="100%",
            ),
        )
    )
    return section_panel(
        rx.vstack(
            *children,
            spacing="3",
            width="100%",
            align="stretch",
        ),
        class_name=class_name,
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
        role="region",
        aria_label="Consultas de " + day["day_label"] + " " + day["date_label"],
        tab_index=0,
        class_name="vitta-agenda-day",
    )


def doctor_week_calendar() -> rx.Component:
    """Reuse the seven-lane calendar visual language from Reception."""
    return section_panel(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon("calendar_days", size=26),
                    class_name="vitta-doctor-week-heading-icon",
                    aria_hidden="true",
                ),
                rx.vstack(
                    rx.heading("Minha semana", size="5"),
                    rx.text("Próximos sete dias de consultas sob sua responsabilidade.",
                            size="2", color="var(--vitta-text-muted)"),
                    spacing="1", align="start", min_width="0",
                ),
                gap="4", align="center", width="100%",
                class_name="vitta-doctor-week-heading",
            ),
            rx.box(
                rx.grid(
                    rx.foreach(DoctorWorkspaceState.calendar_week, _doctor_week_day),
                    columns="7", gap="0.5rem", class_name="vitta-agenda-week-grid",
                ),
                width="100%", overflow_x="auto", class_name="vitta-agenda-week-scroll",
            ),
            spacing="4", align="stretch", width="100%",
            class_name="vitta-doctor-week-content",
        ),
        class_name="vitta-doctor-week-panel",
    )


def doctor_calendar() -> rx.Component:
    return _calendar_grid(
        DoctorWorkspaceState.calendar_cells,
        DoctorWorkspaceState.month_label,
        DoctorWorkspaceState.previous_month,
        DoctorWorkspaceState.next_month,
        heading="Calendário do mês",
        class_name="vitta-doctor-calendar-panel",
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
            rx.hstack(
                rx.box(
                    rx.icon("users", size=31),
                    class_name="vitta-doctor-patient-heading-icon",
                    aria_hidden="true",
                ),
                rx.vstack(
                    rx.heading("Pacientes vinculados às suas consultas", size="5"),
                    rx.text(
                        "Esta lista inclui somente pessoas com consulta associada ao seu cadastro profissional.",
                        size="2",
                        color="var(--vitta-text-muted)",
                    ),
                    spacing="1", align="start", min_width="0",
                ),
                gap="4", align="center", width="100%",
                class_name="vitta-doctor-patient-heading",
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
                    rx.box(
                        empty_state(
                            "users", "Ainda não há pacientes vinculados",
                            "Pacientes aparecem após serem associados a uma consulta sua.",
                            min_height="16rem",
                        ),
                        width="100%", class_name="vitta-doctor-patient-empty",
                    ),
                ),
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        class_name="vitta-doctor-patient-list",
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
    """Compact, accessible administrator form; Vitta One branding is unchanged."""
    return rx.box(
        section_panel(
            rx.vstack(
                rx.flex(
                    rx.hstack(
                        rx.box(
                            rx.icon("settings", size=26),
                            class_name="vitta-admin-action-icon vitta-clinic-settings-icon",
                            aria_hidden="true",
                        ),
                        rx.vstack(
                            rx.heading("Informações da clínica", size="5"),
                            rx.text(
                                "Nome e endereço exibidos nas informações de atendimento do portal do paciente.",
                                size="2", color="var(--vitta-text-muted)",
                            ),
                            spacing="1", align="start", min_width="0",
                        ),
                        align="center", gap="6", min_width="0",
                    ),
                    rx.badge(
                        rx.cond(AdminClinicConfigurationState.configured, "Configurado", "Não configurado"),
                        color_scheme=rx.cond(AdminClinicConfigurationState.configured, "green", "gray"),
                        variant="soft",
                    ),
                    justify="between", align="center", gap="3",
                    width="100%",
                    class_name="vitta-clinic-settings-heading",
                ),
                feedback_region(
                    AdminClinicConfigurationState.error_message,
                    AdminClinicConfigurationState.success_message,
                    element_id="clinic-configuration-feedback",
                ),
                rx.cond(
                    AdminClinicConfigurationState.is_loading,
                    rx.center(
                        rx.hstack(
                            rx.spinner(size="2"),
                            rx.text("Carregando configurações…", size="2"),
                            spacing="2", align="center",
                        ),
                        min_height="9rem", role="status", aria_live="polite",
                    ),
                    rx.cond(
                        AdminClinicConfigurationState.load_failed,
                        rx.button(
                            "Tentar novamente", type="button", variant="outline",
                            on_click=AdminClinicConfigurationState.load,
                        ),
                        rx.form(
                            rx.vstack(
                                rx.box(
                                    field_label("Nome da clínica *", "clinic-configuration-name"),
                                    rx.input(
                                        id="clinic-configuration-name", name="name",
                                        value=AdminClinicConfigurationState.clinic_name,
                                        on_change=AdminClinicConfigurationState.set_clinic_name,
                                        class_name="vitta-input",
                                        max_length=160, aria_required=True,
                                        placeholder="Ex.: Clínica Vitta One",
                                        aria_invalid=AdminClinicConfigurationState.name_error != "",
                                        aria_describedby=rx.cond(
                                            AdminClinicConfigurationState.name_error != "",
                                            "clinic-configuration-name-error", "",
                                        ),
                                        margin_top="0.55rem", width="100%",
                                    ),
                                    rx.cond(
                                        AdminClinicConfigurationState.name_error != "",
                                        rx.text(
                                            AdminClinicConfigurationState.name_error,
                                            id="clinic-configuration-name-error",
                                            role="alert", size="2", color="var(--vitta-danger)",
                                            margin_top="0.4rem",
                                        ),
                                        rx.fragment(),
                                    ),
                                    width="100%",
                                ),
                                rx.box(
                                    field_label("Endereço da clínica *", "clinic-configuration-address"),
                                    rx.text_area(
                                        id="clinic-configuration-address", name="address",
                                        value=AdminClinicConfigurationState.clinic_address,
                                        on_change=AdminClinicConfigurationState.set_clinic_address,
                                        class_name="vitta-textarea",
                                        max_length=500, aria_required=True,
                                        placeholder="Ex.: Rua das Flores, 123 — Centro, Cidade — UF",
                                        aria_invalid=AdminClinicConfigurationState.address_error != "",
                                        aria_describedby=rx.cond(
                                            AdminClinicConfigurationState.address_error != "",
                                            "clinic-configuration-address-error", "",
                                        ),
                                        rows="3", resize="vertical",
                                        margin_top="0.55rem", width="100%",
                                    ),
                                    rx.cond(
                                        AdminClinicConfigurationState.address_error != "",
                                        rx.text(
                                            AdminClinicConfigurationState.address_error,
                                            id="clinic-configuration-address-error",
                                            role="alert", size="2", color="var(--vitta-danger)",
                                            margin_top="0.4rem",
                                        ),
                                        rx.fragment(),
                                    ),
                                    width="100%",
                                ),
                                rx.flex(
                                    rx.link("Cancelar", href="/admin",
                                            class_name="vitta-context-link"),
                                    rx.button(
                                        rx.cond(
                                            AdminClinicConfigurationState.is_saving,
                                            "Salvando alterações…", "Salvar alterações",
                                        ),
                                        type="submit", class_name="vitta-primary-action",
                                        disabled=AdminClinicConfigurationState.is_saving,
                                        loading=AdminClinicConfigurationState.is_saving,
                                    ),
                                    justify="end", align="center", gap="0.75rem",
                                    flex_wrap="wrap", width="100%",
                                    class_name="vitta-clinic-settings-actions",
                                ),
                                spacing="5", align="stretch", width="100%",
                            ),
                            on_submit=AdminClinicConfigurationState.save,
                            reset_on_submit=False,
                            margin_top="1.25rem",
                            width="100%",
                        ),
                    ),
                ),
                spacing="3", align="stretch", width="100%",
            ),
            padding=rx.breakpoints(initial="1rem", sm="1.75rem 2rem"),
        ),
        width="100%",
        class_name="vitta-clinic-settings-form",
    )
