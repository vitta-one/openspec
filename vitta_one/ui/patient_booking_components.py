"""Accessible, responsive patient self-booking in the native Vitta-One design system."""
import reflex as rx

from vitta_one.patient_portal.booking_state import PatientBookingState
from vitta_one.ui.components import empty_state, feedback_region, field_label, section_panel


def _specialty_select() -> rx.Component:
    return rx.box(
        field_label("1. Especialidade", "patient-booking-specialty"),
        rx.select.root(
            rx.select.trigger(
                id="patient-booking-specialty", width="100%",
                placeholder="Escolha uma especialidade",
                aria_label="Escolha a especialidade para sua consulta",
            ),
            rx.select.content(
                rx.select.item("Selecione uma especialidade", value="__none__"),
                rx.foreach(
                    PatientBookingState.specialties,
                    lambda option: rx.select.item(
                        option["label"], value=option["value"]
                    ),
                ),
                position="popper",
            ),
            value=PatientBookingState.selected_specialty,
            on_change=PatientBookingState.choose_specialty,
            disabled=PatientBookingState.is_loading | PatientBookingState.is_submitting,
        ),
        width="100%",
    )


def _doctor_select() -> rx.Component:
    return rx.box(
        field_label("2. Médico", "patient-booking-doctor"),
        rx.select.root(
            rx.select.trigger(
                id="patient-booking-doctor", width="100%",
                placeholder="Escolha um médico",
                aria_label="Escolha o médico para sua consulta",
            ),
            rx.select.content(
                rx.select.item("Selecione um médico", value="__none__"),
                rx.foreach(
                    PatientBookingState.doctors,
                    lambda option: rx.select.item(
                        option["label"], value=option["value"]
                    ),
                ),
                position="popper",
            ),
            value=PatientBookingState.selected_doctor,
            on_change=PatientBookingState.choose_doctor,
            disabled=(PatientBookingState.selected_specialty == "__none__")
                | PatientBookingState.is_loading | PatientBookingState.is_submitting,
        ),
        rx.cond(
            (PatientBookingState.selected_specialty != "__none__")
            & ~PatientBookingState.has_doctors
            & ~PatientBookingState.is_loading,
            rx.text(
                "Não há médicos ativos cadastrados para esta especialidade.",
                size="2", color="var(--vitta-text-muted)", margin_top="0.6rem",
                role="status",
            ),
            rx.fragment(),
        ),
        width="100%",
    )


def _slot_row(slot) -> rx.Component:
    return rx.flex(
        rx.hstack(
            rx.icon("clock", size=17, color="var(--vitta-primary)"),
            rx.text(slot["hour"], font_weight="750", size="3",
                    class_name="vitta-tabular"),
            spacing="2", align="center",
        ),
        rx.button(
            "Selecionar horário",
            type="button",
            size="2",
            variant="outline",
            color_scheme="teal",
            on_click=PatientBookingState.review_slot(slot["id"]),
            disabled=PatientBookingState.is_submitting
                | PatientBookingState.is_loading,
            aria_label="Selecionar horário de " + slot["label"],
        ),
        direction=rx.breakpoints(initial="column", sm="row"),
        align=rx.breakpoints(initial="stretch", sm="center"),
        justify="between", gap="3", width="100%",
        padding="0.8rem 0.9rem",
        border="1px solid var(--vitta-border)",
        border_radius="0.8rem",
    )


def _time_slots() -> rx.Component:
    return rx.vstack(
        rx.flex(
            rx.box(
                rx.heading("3. Escolha o horário", size="4"),
                rx.text(
                    "Horários disponíveis para os próximos 45 dias. "
                    "A reserva é confirmada somente após sua revisão.",
                    color="var(--vitta-text-muted)", size="2",
                    margin_top="0.35rem", line_height="1.5",
                ),
            ),
            rx.badge("Horários da clínica", variant="soft", color_scheme="teal"),
            align="center", justify="between", gap="2",
            flex_wrap="wrap", width="100%",
        ),
        rx.cond(
            PatientBookingState.selected_doctor == "__none__",
            empty_state(
                "calendar_days", "Selecione um médico",
                "Escolha a especialidade e o médico acima para ver a disponibilidade.",
            ),
            rx.cond(
                PatientBookingState.is_loading,
                rx.center(
                    rx.spinner(size="3"),
                    rx.text("Buscando horários disponíveis…", role="status"),
                    min_height="7rem", gap="3",
                ),
                rx.cond(
                    PatientBookingState.has_slots,
                    rx.vstack(
                        rx.foreach(
                            PatientBookingState.slot_groups,
                            lambda day: rx.box(
                                rx.heading(
                                    day["date"], size="3",
                                    margin_bottom="0.8rem",
                                    class_name="vitta-tabular",
                                ),
                                rx.vstack(
                                    rx.foreach(day["slots"], _slot_row),
                                    spacing="2", width="100%",
                                ),
                                padding="1rem",
                                border="1px solid var(--vitta-border)",
                                border_radius="0.9rem",
                                width="100%",
                            ),
                        ),
                        align="stretch", spacing="3", width="100%",
                    ),
                    empty_state(
                        "calendar_x", "Nenhum horário livre neste período",
                        "Escolha outro médico ou peça orientação à recepção.",
                    ),
                ),
            ),
        ),
        align="stretch", spacing="4", width="100%",
    )


def _review_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Confirmar agendamento"),
            rx.dialog.description(
                "Revise os dados. Após confirmar, o horário aparecerá na sua "
                "agenda e na agenda do médico.",
                margin_top="0.4rem", margin_bottom="1rem",
            ),
            rx.box(
                rx.text(
                    PatientBookingState.selected_doctor_name,
                    font_weight="750", size="3",
                ),
                rx.text(
                    PatientBookingState.selected_slot_label,
                    size="2", margin_top="0.35rem",
                    class_name="vitta-tabular",
                ),
                padding="1rem", border_radius="0.8rem",
                background="var(--vitta-surface-muted)",
                width="100%",
            ),
            rx.flex(
                rx.button(
                    "Voltar e escolher outro",
                    type="button", variant="outline",
                    color_scheme="gray",
                    on_click=PatientBookingState.cancel_confirmation,
                    disabled=PatientBookingState.is_submitting,
                ),
                rx.button(
                    "Confirmar consulta", type="button",
                    color_scheme="teal", high_contrast=True,
                    on_click=PatientBookingState.confirm_booking,
                    disabled=PatientBookingState.is_submitting,
                    loading=PatientBookingState.is_submitting,
                    id="patient-booking-confirm",
                ),
                direction=rx.breakpoints(initial="column-reverse", sm="row"),
                justify="end", gap="3", margin_top="1.25rem",
                width="100%",
            ),
            max_width="36rem", class_name="vitta-dialog-content",
        ),
        open=PatientBookingState.confirmation_open,
        on_open_change=PatientBookingState.set_confirmation_open,
    )


def patient_booking_workspace() -> rx.Component:
    return rx.vstack(
        feedback_region(
            PatientBookingState.error_message,
            PatientBookingState.success_message,
            "patient-booking-feedback",
        ),
        rx.cond(
            PatientBookingState.booked,
            section_panel(
                rx.vstack(
                    rx.icon("circle_check_big", size=36,
                            color="var(--vitta-primary)"),
                    rx.heading("Consulta agendada!", size="5"),
                    rx.text(
                        "Seu agendamento foi registrado. Confira os detalhes "
                        "em Minhas consultas.",
                        color="var(--vitta-text-muted)", line_height="1.55",
                    ),
                    rx.text(
                        PatientBookingState.booked_description,
                        font_weight="750", class_name="vitta-tabular",
                    ),
                    rx.link(
                        rx.button(
                            "Ver minhas consultas", color_scheme="teal",
                            high_contrast=True, min_height="2.8rem",
                        ),
                        href="/paciente",
                    ),
                    spacing="3", align="start", width="100%",
                ),
            ),
            rx.vstack(
                section_panel(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("stethoscope", size=20,
                                    color="var(--vitta-primary)"),
                            rx.heading("Encontre seu atendimento", size="4"),
                            spacing="2", align="center",
                        ),
                        rx.text(
                            "Escolha primeiro a especialidade, depois o médico. "
                            "Você verá apenas os horários que a clínica disponibilizou.",
                            size="2", color="var(--vitta-text-muted)",
                            line_height="1.5",
                        ),
                        rx.flex(
                            _specialty_select(),
                            _doctor_select(),
                            direction=rx.breakpoints(initial="column", md="row"),
                            align="start", gap="4", width="100%",
                        ),
                        spacing="4", align="stretch", width="100%",
                    )
                ),
                section_panel(_time_slots()),
                _review_dialog(),
                align="stretch", spacing="4", width="100%",
            ),
        ),
        align="stretch", spacing="4", width="100%",
    )
