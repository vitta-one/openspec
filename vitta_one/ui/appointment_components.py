"""Simple operational UI for availability and appointment scheduling."""

import reflex as rx

from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus
from vitta_one.appointment_scheduling.state import AdminAvailabilityState, ReceptionAgendaState
from vitta_one.ui.components import empty_state, feedback_region, field_label, section_panel
from vitta_one.ui.queue_components import priority_select


def _professional_select(
    *,
    control_id: str,
    value,
    on_change,
    include_all: bool,
    disabled=False,
) -> rx.Component:
    first = (
        rx.select.item("Todos os profissionais", value="__all__")
        if include_all
        else rx.select.item("Selecione um profissional", value="__none__")
    )
    options = (
        AdminAvailabilityState.professionals
        if control_id.startswith("admin")
        else ReceptionAgendaState.professionals
    )
    return rx.select.root(
        rx.select.trigger(id=control_id, width="100%", class_name="vitta-select-trigger"),
        rx.select.content(
            first,
            rx.foreach(options, lambda item: rx.select.item(item["label"], value=item["value"])),
            position="popper",
        ),
        value=value,
        on_change=on_change,
        disabled=disabled,
        size="3",
    )


def _slot_status_badge(status, label) -> rx.Component:
    return rx.cond(
        status == AvailabilitySlotStatus.AVAILABLE.value,
        rx.badge(label, color_scheme="green", variant="soft", high_contrast=True),
        rx.cond(
            status == AvailabilitySlotStatus.BOOKED.value,
            rx.badge(label, color_scheme="blue", variant="soft", high_contrast=True),
            rx.badge(label, color_scheme="gray", variant="soft"),
        ),
    )


def consultation_status_badge(
    status, label, *, class_name: str | None = None
) -> rx.Component:
    """Canonical badge for a persisted consultation status."""
    return rx.match(
        status,
        (
            ConsultationStatus.AGENDADA.value,
            rx.badge(
                label,
                color_scheme="blue",
                variant="soft",
                high_contrast=True,
                class_name=class_name,
            ),
        ),
        (
            ConsultationStatus.CONFIRMADA.value,
            rx.badge(
                label,
                color_scheme="teal",
                variant="soft",
                high_contrast=True,
                class_name=class_name,
            ),
        ),
        (
            ConsultationStatus.EM_ANDAMENTO.value,
            rx.badge(
                label,
                color_scheme="amber",
                variant="soft",
                high_contrast=True,
                class_name=class_name,
            ),
        ),
        (
            ConsultationStatus.CONCLUIDA.value,
            rx.badge(
                label,
                color_scheme="green",
                variant="soft",
                high_contrast=True,
                class_name=class_name,
            ),
        ),
        (
            ConsultationStatus.CANCELADA.value,
            rx.badge(
                label,
                color_scheme="red",
                variant="soft",
                high_contrast=True,
                class_name=class_name,
            ),
        ),
        rx.badge(
            label,
            color_scheme="gray",
            variant="soft",
            class_name=class_name,
        ),
    )


def _consultation_status_badge(status, label) -> rx.Component:
    """Backward-compatible private name for existing consumers."""
    return consultation_status_badge(status, label)

def _admin_slot_row(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.hstack(
                rx.box(rx.icon("calendar_clock", size=18), class_name="vitta-patient-avatar"),
                rx.box(
                    rx.text(row["time_label"], font_weight="750", size="4", class_name="vitta-tabular"),
                    rx.text(row["professional_name"], size="1", color="var(--vitta-text-muted)", margin_top="0.15rem"),
                ),
                spacing="3",
                align="center",
                min_width="0",
            ),
            rx.hstack(
                _slot_status_badge(row["status"], row["status_label"]),
                rx.cond(
                    row["status"] == AvailabilitySlotStatus.BOOKED.value,
                    rx.text("Gerenciado pela Recepção", size="1", color="var(--vitta-text-subtle)"),
                    rx.button(
                        rx.cond(
                            row["status"] == AvailabilitySlotStatus.INACTIVE.value,
                            "Reativar",
                            "Desativar",
                        ),
                        type="button",
                        variant="outline",
                        color_scheme="teal",
                        size="2",
                        on_click=AdminAvailabilityState.toggle_slot(row["id"], row["status"]),
                        disabled=AdminAvailabilityState.is_submitting,
                    ),
                ),
                spacing="2",
                align="center",
                flex_wrap="wrap",
            ),
            direction=rx.breakpoints(initial="column", md="row"),
            align=rx.breakpoints(initial="stretch", md="center"),
            justify="between",
            gap="0.75rem",
            width="100%",
        ),
        class_name="vitta-schedule-row",
        role="listitem",
    )


def _admin_slot_day(day) -> rx.Component:
    return rx.box(
        rx.heading(day["date_label"], size="3", color="var(--vitta-text)", margin_bottom="0.75rem"),
        rx.vstack(
            rx.foreach(day["slots"], _admin_slot_row),
            spacing="2", width="100%", align="stretch", role="list",
        ),
        width="100%", class_name="vitta-day-group",
    )


def _reception_slot_day(day) -> rx.Component:
    return rx.box(
        rx.heading(day["date_label"], size="3", margin_bottom="0.75rem"),
        rx.vstack(
            rx.foreach(day["slots"], _available_slot_row),
            spacing="2", width="100%", align="stretch", role="list",
        ),
        width="100%", class_name="vitta-day-group",
    )


def admin_availability_panel() -> rx.Component:
    """Administrator availability surface: explicit slots, no calendar complexity."""
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.text("AGENDA", class_name="vitta-section-kicker"),
                    rx.heading("Horários de atendimento", size="5", margin_top="0.25rem"),
                    rx.text(
                        "Escolha um profissional, a data e a hora em que ele poderá atender. Veja abaixo os horários já cadastrados.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        line_height="1.55",
                        margin_top="0.35rem",
                        max_width="72ch",
                    ),
                ),
                rx.badge("Horários disponíveis", color_scheme="teal", variant="soft"),
                direction=rx.breakpoints(initial="column", md="row"),
                justify="between",
                align=rx.breakpoints(initial="stretch", md="start"),
                gap="0.75rem",
                width="100%",
            ),
            feedback_region(
                AdminAvailabilityState.error_message,
                AdminAvailabilityState.success_message,
                "availability-feedback",
            ),
            rx.el.form(
                rx.grid(
                    rx.box(
                        field_label("Profissional", "admin-slot-professional"),
                        rx.box(
                            _professional_select(
                                control_id="admin-slot-professional",
                                value=AdminAvailabilityState.selected_professional,
                                on_change=AdminAvailabilityState.update_selected_professional,
                                include_all=False,
                                disabled=AdminAvailabilityState.is_submitting,
                            ),
                            margin_top="0.4rem",
                        ),
                    ),
                    rx.box(
                        field_label("Data do atendimento", "admin-slot-date"),
                        rx.el.input(
                            id="admin-slot-date",
                            name="date",
                            type="date",
                            value=AdminAvailabilityState.slot_date_local,
                            on_change=AdminAvailabilityState.update_slot_date,
                            required=True,
                            class_name="vitta-input",
                            margin_top="0.4rem",
                        ),
                    ),
                    rx.box(
                        field_label("Hora do atendimento", "admin-slot-time"),
                        rx.el.input(
                            id="admin-slot-time",
                            name="time",
                            type="time",
                            value=AdminAvailabilityState.slot_time_local,
                            on_change=AdminAvailabilityState.update_slot_time,
                            required=True,
                            class_name="vitta-input",
                            margin_top="0.4rem",
                        ),
                    ),
                    rx.button(
                        rx.hstack(rx.icon("plus", size=17), rx.text("Adicionar horário"), spacing="2", align="center"),
                        type="submit",
                        color_scheme="teal",
                        high_contrast=True,
                        min_height="3rem",
                        align_self="end",
                        disabled=AdminAvailabilityState.is_submitting | ~AdminAvailabilityState.has_professionals,
                        loading=AdminAvailabilityState.is_submitting,
                    ),
                    columns=rx.breakpoints(initial="1", md="repeat(2, minmax(0, 1fr))", xl="minmax(13rem, 1.5fr) minmax(9rem, 1fr) minmax(9rem, 1fr) auto"),
                    gap="0.75rem",
                    align_items="end",
                    width="100%",
                ),
                on_submit=AdminAvailabilityState.create_slot,
                no_validate=False,
                width="100%",
            ),
            rx.box(
                rx.grid(
                    rx.box(
                        field_label("Filtrar profissional", "admin-filter-professional"),
                        rx.box(
                            _professional_select(
                                control_id="admin-filter-professional",
                                value=AdminAvailabilityState.filter_professional,
                                on_change=AdminAvailabilityState.update_filter_professional,
                                include_all=True,
                                disabled=AdminAvailabilityState.is_loading,
                            ),
                            margin_top="0.4rem",
                        ),
                    ),
                    rx.box(
                        field_label("Data inicial", "admin-filter-start"),
                        rx.el.input(
                            id="admin-filter-start",
                            type="date",
                            value=AdminAvailabilityState.filter_start_date,
                            on_change=AdminAvailabilityState.update_filter_start_date,
                            class_name="vitta-input",
                            margin_top="0.4rem",
                        ),
                    ),
                    rx.box(
                        field_label("Data final", "admin-filter-end"),
                        rx.el.input(
                            id="admin-filter-end",
                            type="date",
                            value=AdminAvailabilityState.filter_end_date,
                            on_change=AdminAvailabilityState.update_filter_end_date,
                            class_name="vitta-input",
                            margin_top="0.4rem",
                        ),
                    ),
                    rx.button(
                        "Aplicar filtros",
                        type="button",
                        variant="outline",
                        color_scheme="teal",
                        min_height="3rem",
                        align_self="end",
                        on_click=AdminAvailabilityState.refresh,
                        disabled=AdminAvailabilityState.is_loading,
                    ),
                    columns=rx.breakpoints(initial="1", lg="minmax(14rem, 1fr) 10rem 10rem auto"),
                    gap="0.65rem",
                    align_items="end",
                    width="100%",
                ),
                class_name="vitta-filter-strip",
            ),
            rx.cond(
                AdminAvailabilityState.is_loading,
                rx.center(rx.spinner(size="3"), min_height="8rem", width="100%", role="status", aria_live="polite"),
                rx.cond(
                    AdminAvailabilityState.has_slots,
                    rx.vstack(
                        rx.foreach(AdminAvailabilityState.slots_by_day, _admin_slot_day),
                        spacing="2",
                        align="stretch",
                        width="100%",
                        role="list",
                    ),
                    empty_state(
                        "calendar",
                        "Nenhum horário neste período",
                        "Adicione um horário futuro ou ajuste os filtros.",
                    ),
                ),
            ),
            spacing="4",
            align="stretch",
            width="100%",
        )
    )


def _available_slot_row(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["time_label"], font_weight="750", size="4", class_name="vitta-tabular"),
                rx.text(row["professional_name"], size="1", color="var(--vitta-text-muted)", margin_top="0.15rem"),
            ),
            rx.button(
                "Agendar",
                type="button",
                color_scheme="teal",
                high_contrast=True,
                size="2",
                on_click=ReceptionAgendaState.schedule(row["id"]),
                disabled=(ReceptionAgendaState.selected_patient_id == 0) | ReceptionAgendaState.is_submitting,
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            align=rx.breakpoints(initial="stretch", sm="center"),
            justify="between",
            gap="0.65rem",
            width="100%",
        ),
        class_name="vitta-schedule-row",
        role="listitem",
    )


def _consultation_actions(row) -> rx.Component:
    return rx.match(
        row["status"],
        (
            ConsultationStatus.AGENDADA.value,
            rx.hstack(
                rx.button(
                    "Confirmar chegada",
                    type="button",
                    color_scheme="teal",
                    high_contrast=True,
                    size="2",
                    on_click=ReceptionAgendaState.begin_arrival(
                        row["id"],
                        row["patient_name"],
                        row["professional_name"],
                        row["scheduled_at"],
                    ),
                    disabled=ReceptionAgendaState.is_submitting,
                ),
                rx.button(
                    "Reagendar",
                    type="button",
                    variant="outline",
                    color_scheme="teal",
                    size="2",
                    on_click=ReceptionAgendaState.begin_reschedule(
                        row["id"], row["patient_name"]
                    ),
                    disabled=ReceptionAgendaState.is_submitting,
                ),
                rx.button(
                    "Cancelar",
                    type="button",
                    variant="ghost",
                    color_scheme="red",
                    size="2",
                    on_click=ReceptionAgendaState.begin_cancel(
                        row["id"], row["patient_name"], row["scheduled_at"]
                    ),
                    disabled=ReceptionAgendaState.is_submitting,
                ),
                spacing="2",
                align="center",
                flex_wrap="wrap",
            ),
        ),
        (
            ConsultationStatus.CONFIRMADA.value,
            rx.hstack(
                rx.icon("users", size=15),
                rx.text("Paciente na fila", size="1", font_weight="700"),
                spacing="2",
                align="center",
                color="var(--vitta-primary)",
            ),
        ),
        (
            ConsultationStatus.EM_ANDAMENTO.value,
            rx.hstack(
                rx.icon("stethoscope", size=15),
                rx.text("Atendimento em andamento", size="1", font_weight="700"),
                spacing="2",
                align="center",
                color="var(--vitta-warning)",
            ),
        ),
        rx.text("Somente histórico", size="1", color="var(--vitta-text-subtle)"),
    )


def _consultation_row(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.hstack(
                    rx.text(
                        row["scheduled_at"],
                        font_weight="750",
                        size="2",
                        class_name="vitta-tabular",
                    ),
                    consultation_status_badge(row["status"], row["status_label"]),
                    spacing="2",
                    align="center",
                    flex_wrap="wrap",
                ),
                rx.text(row["patient_name"], size="2", margin_top="0.35rem"),
                rx.text(
                    row["professional_name"],
                    size="1",
                    color="var(--vitta-text-muted)",
                    margin_top="0.15rem",
                ),
            ),
            _consultation_actions(row),
            direction=rx.breakpoints(initial="column", md="row"),
            align=rx.breakpoints(initial="stretch", md="center"),
            justify="between",
            gap="0.75rem",
            width="100%",
        ),
        class_name="vitta-schedule-row",
        role="listitem",
    )


def _arrival_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Confirmar chegada"),
            rx.dialog.description(
                "Confirme que o paciente chegou à clínica. Informe somente o relato recebido e a prioridade definida pela operação.",
                margin_top="0.35rem",
                margin_bottom="1rem",
            ),
            rx.box(
                rx.text(
                    ReceptionAgendaState.arrival_patient_name,
                    font_weight="800",
                    size="3",
                ),
                rx.text(
                    ReceptionAgendaState.arrival_professional_name,
                    size="2",
                    color="var(--vitta-text-muted)",
                    margin_top="0.2rem",
                ),
                rx.text(
                    ReceptionAgendaState.arrival_scheduled_at,
                    size="1",
                    color="var(--vitta-text-subtle)",
                    class_name="vitta-tabular",
                    margin_top="0.15rem",
                ),
                class_name="vitta-info-strip",
                margin_bottom="1rem",
            ),
            rx.el.form(
                rx.vstack(
                    rx.box(
                        field_label("Sintomas relatados", "arrival-symptoms"),
                        rx.el.textarea(
                            id="arrival-symptoms",
                            name="symptoms",
                            required=True,
                            max_length=4000,
                            rows=4,
                            value=ReceptionAgendaState.arrival_symptoms,
                            on_change=ReceptionAgendaState.update_arrival_symptoms,
                            class_name="vitta-textarea",
                            aria_describedby="arrival-help",
                            margin_top="0.4rem",
                            auto_focus=True,
                        ),
                        rx.text(
                            "Registre o relato recebido. O Vitta-One não infere sintomas nem gravidade clínica.",
                            id="arrival-help",
                            size="1",
                            color="var(--vitta-text-muted)",
                            line_height="1.45",
                            margin_top="0.35rem",
                        ),
                        width="100%",
                    ),
                    rx.box(
                        field_label("Prioridade informada", "arrival-priority"),
                        priority_select(
                            name="priority",
                            control_id="arrival-priority",
                            value=ReceptionAgendaState.arrival_priority,
                            on_change=ReceptionAgendaState.update_arrival_priority,
                            described_by="arrival-priority-help",
                            disabled=ReceptionAgendaState.is_submitting,
                        ),
                        rx.text(
                            "Escolha exatamente a classificação recebida: Vermelho, Amarelo ou Verde.",
                            id="arrival-priority-help",
                            size="1",
                            color="var(--vitta-text-muted)",
                            margin_top="0.4rem",
                        ),
                        width="100%",
                    ),
                    rx.flex(
                        rx.dialog.close(
                            rx.button(
                                "Voltar",
                                type="button",
                                variant="ghost",
                                disabled=ReceptionAgendaState.is_submitting,
                            )
                        ),
                        rx.button(
                            "Confirmar chegada",
                            type="submit",
                            color_scheme="teal",
                            high_contrast=True,
                            disabled=ReceptionAgendaState.is_submitting,
                            loading=ReceptionAgendaState.is_submitting,
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
                on_submit=ReceptionAgendaState.confirm_arrival,
                no_validate=True,
                width="100%",
            ),
            class_name="vitta-dialog-content",
            max_width="38rem",
        ),
        open=ReceptionAgendaState.arrival_dialog_open,
        on_open_change=ReceptionAgendaState.set_arrival_dialog_open,
    )

def _reschedule_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Reagendar consulta"),
            rx.dialog.description(
                "Escolha outro horário disponível. O paciente será mantido.",
                margin_top="0.35rem",
                margin_bottom="1rem",
            ),
            rx.text(
                ReceptionAgendaState.reschedule_patient_name,
                font_weight="750",
                margin_bottom="0.8rem",
            ),
            field_label("Novo horário", "reception-new-slot"),
            rx.select.root(
                rx.select.trigger(id="reception-new-slot", width="100%", margin_top="0.4rem"),
                rx.select.content(
                    rx.select.item("Selecione um horário", value="__none__"),
                    rx.foreach(
                        ReceptionAgendaState.available_slots,
                        lambda row: rx.select.item(
                            row["starts_at"] + " · " + row["professional_name"],
                            value=row["value"],
                        ),
                    ),
                    position="popper",
                ),
                value=ReceptionAgendaState.selected_new_slot,
                on_change=ReceptionAgendaState.update_new_slot,
                disabled=ReceptionAgendaState.is_submitting,
                size="3",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button("Voltar", type="button", variant="ghost", disabled=ReceptionAgendaState.is_submitting)
                ),
                rx.button(
                    "Confirmar reagendamento",
                    type="button",
                    color_scheme="teal",
                    high_contrast=True,
                    on_click=ReceptionAgendaState.confirm_reschedule,
                    disabled=(ReceptionAgendaState.selected_new_slot == "__none__") | ReceptionAgendaState.is_submitting,
                    loading=ReceptionAgendaState.is_submitting,
                ),
                justify="end",
                gap="0.5rem",
                direction=rx.breakpoints(initial="column-reverse", sm="row"),
                width="100%",
                margin_top="1rem",
            ),
            class_name="vitta-dialog-content",
            max_width="38rem",
        ),
        open=ReceptionAgendaState.reschedule_dialog_open,
        on_open_change=ReceptionAgendaState.set_reschedule_dialog_open,
    )


def _cancel_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Cancelar consulta"),
            rx.dialog.description(
                "A consulta permanecerá no histórico e o horário voltará a ficar disponível quando ainda for futuro.",
                margin_top="0.35rem",
            ),
            rx.box(
                rx.text(ReceptionAgendaState.cancel_patient_name, font_weight="750"),
                rx.text(
                    ReceptionAgendaState.cancel_scheduled_at,
                    size="2",
                    color="var(--vitta-text-muted)",
                    margin_top="0.2rem",
                ),
                class_name="vitta-info-strip",
                margin_top="1rem",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button("Manter consulta", type="button", variant="ghost", disabled=ReceptionAgendaState.is_submitting)
                ),
                rx.button(
                    "Cancelar consulta",
                    type="button",
                    color_scheme="red",
                    high_contrast=True,
                    on_click=ReceptionAgendaState.confirm_cancel,
                    disabled=ReceptionAgendaState.is_submitting,
                    loading=ReceptionAgendaState.is_submitting,
                ),
                justify="end",
                gap="0.5rem",
                direction=rx.breakpoints(initial="column-reverse", sm="row"),
                width="100%",
                margin_top="1rem",
            ),
            class_name="vitta-dialog-content",
            max_width="34rem",
        ),
        open=ReceptionAgendaState.cancel_dialog_open,
        on_open_change=ReceptionAgendaState.set_cancel_dialog_open,
    )


def reception_agenda_panel() -> rx.Component:
    """Reception agenda kept intentionally simple: filters, patient, slots and history."""
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.text("AGENDA", class_name="vitta-section-kicker"),
                    rx.heading("Agendamentos", size="5", margin_top="0.25rem"),
                    rx.text(
                        "Localize o paciente, escolha um horário disponível e acompanhe as consultas do período.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        line_height="1.55",
                        margin_top="0.35rem",
                    ),
                ),
                rx.fragment(),
                direction=rx.breakpoints(initial="column", md="row"),
                justify="between",
                align=rx.breakpoints(initial="stretch", md="start"),
                gap="0.75rem",
                width="100%",
            ),
            feedback_region(
                ReceptionAgendaState.error_message,
                ReceptionAgendaState.success_message,
                "agenda-feedback",
            ),
            rx.grid(
                rx.box(
                    field_label("Profissional", "reception-filter-professional"),
                    rx.box(
                        _professional_select(
                            control_id="reception-filter-professional",
                            value=ReceptionAgendaState.filter_professional,
                            on_change=ReceptionAgendaState.update_filter_professional,
                            include_all=True,
                            disabled=ReceptionAgendaState.is_loading,
                        ),
                        margin_top="0.4rem",
                    ),
                ),
                rx.box(
                    field_label("Data inicial", "reception-filter-start"),
                    rx.el.input(
                        id="reception-filter-start",
                        type="date",
                        value=ReceptionAgendaState.filter_start_date,
                        on_change=ReceptionAgendaState.update_filter_start_date,
                        class_name="vitta-input",
                        margin_top="0.4rem",
                    ),
                ),
                rx.box(
                    field_label("Data final", "reception-filter-end"),
                    rx.el.input(
                        id="reception-filter-end",
                        type="date",
                        value=ReceptionAgendaState.filter_end_date,
                        on_change=ReceptionAgendaState.update_filter_end_date,
                        class_name="vitta-input",
                        margin_top="0.4rem",
                    ),
                ),
                rx.button(
                    "Aplicar filtros",
                    type="button",
                    variant="outline",
                    color_scheme="teal",
                    min_height="3rem",
                    align_self="end",
                    on_click=ReceptionAgendaState.refresh,
                    disabled=ReceptionAgendaState.is_loading,
                ),
                columns=rx.breakpoints(initial="1", lg="minmax(14rem, 1fr) 10rem 10rem auto"),
                gap="0.65rem",
                align_items="end",
                width="100%",
                class_name="vitta-filter-strip",
            ),
            rx.el.form(
                rx.flex(
                    rx.box(
                        field_label("CPF do paciente", "agenda-patient-cpf"),
                        rx.el.input(
                            id="agenda-patient-cpf",
                            type="text",
                            input_mode="numeric",
                            auto_complete="off",
                            value=ReceptionAgendaState.patient_cpf,
                            on_change=ReceptionAgendaState.update_patient_cpf,
                            placeholder="Somente números ou CPF formatado",
                            class_name="vitta-input",
                            margin_top="0.4rem",
                        ),
                        flex="1 1 16rem",
                    ),
                    rx.button(
                        "Localizar paciente",
                        type="submit",
                        color_scheme="teal",
                        high_contrast=True,
                        min_height="3rem",
                        align_self="end",
                        disabled=ReceptionAgendaState.is_submitting,
                        loading=ReceptionAgendaState.is_submitting,
                    ),
                    direction=rx.breakpoints(initial="column", sm="row"),
                    align=rx.breakpoints(initial="stretch", sm="end"),
                    gap="0.65rem",
                    width="100%",
                ),
                on_submit=ReceptionAgendaState.find_patient,
                no_validate=True,
                width="100%",
            ),
            rx.cond(
                ReceptionAgendaState.selected_patient_id > 0,
                rx.flex(
                    rx.hstack(
                        rx.icon("user", size=17),
                        rx.text(ReceptionAgendaState.selected_patient_name, font_weight="750", size="2"),
                        spacing="2",
                        align="center",
                    ),
                    rx.button(
                        "Trocar paciente",
                        type="button",
                        variant="ghost",
                        size="2",
                        on_click=ReceptionAgendaState.clear_patient,
                    ),
                    direction=rx.breakpoints(initial="column", sm="row"),
                    justify="between",
                    align=rx.breakpoints(initial="stretch", sm="center"),
                    gap="0.5rem",
                    class_name="vitta-selection-bar",
                    width="100%",
                ),
                rx.box(
                    rx.hstack(
                        rx.icon("info", size=17),
                        rx.text("Localize um paciente para habilitar o agendamento.", size="2"),
                        spacing="2",
                        align="center",
                    ),
                    class_name="vitta-info-strip",
                ),
            ),
            rx.cond(
                ReceptionAgendaState.is_loading,
                rx.center(rx.spinner(size="3"), min_height="10rem", width="100%", role="status", aria_live="polite"),
                rx.grid(
                    rx.box(
                        rx.heading("Horários disponíveis", size="4"),
                        rx.cond(
                            ReceptionAgendaState.has_available_slots,
                            rx.vstack(
                                rx.foreach(ReceptionAgendaState.available_slots_by_day, _reception_slot_day),
                                spacing="2",
                                align="stretch",
                                width="100%",
                                role="list",
                                margin_top="0.8rem",
                            ),
                            empty_state(
                                "calendar",
                                "Sem horários disponíveis",
                                "Tente outro profissional ou período. A Administração poderá adicionar novos horários.",
                            ),
                        ),
                        min_width="0",
                    ),
                    rx.box(
                        rx.heading("Consultas do período", size="4"),
                        rx.cond(
                            ReceptionAgendaState.has_consultations,
                            rx.vstack(
                                rx.foreach(ReceptionAgendaState.consultations, _consultation_row),
                                spacing="2",
                                align="stretch",
                                width="100%",
                                role="list",
                                margin_top="0.8rem",
                            ),
                            empty_state(
                                "calendar_days",
                                "Nenhuma consulta neste período",
                                "Consultas agendadas e canceladas aparecerão aqui sem dados fictícios.",
                            ),
                        ),
                        min_width="0",
                    ),
                    columns=rx.breakpoints(initial="1", xl="minmax(0, 0.85fr) minmax(0, 1.15fr)"),
                    gap="1rem",
                    width="100%",
                    align_items="start",
                ),
            ),
            _arrival_dialog(),
            _reschedule_dialog(),
            _cancel_dialog(),
            spacing="4",
            align="stretch",
            width="100%",
        )
    )
