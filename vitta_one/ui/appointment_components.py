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
    """A compact daily row with a confirmation before making a slot unavailable."""
    return rx.flex(
        rx.hstack(
            rx.text(row["time_label"], font_weight="750", size="3", class_name="vitta-tabular"),
            _slot_status_badge(row["status"], row["status_label"]),
            spacing="3",
            align="center",
        ),
        rx.cond(
            row["status"] == AvailabilitySlotStatus.BOOKED.value,
            rx.text("Reserva existente — gerenciar pela Recepção", size="2",
                    color="var(--vitta-text-muted)"),
            rx.cond(
                row["status"] == AvailabilitySlotStatus.INACTIVE.value,
                rx.button(
                    "Reativar", type="button", variant="outline", color_scheme="teal",
                    size="2", on_click=AdminAvailabilityState.toggle_slot(row["id"], row["status"]),
                    disabled=AdminAvailabilityState.is_submitting,
                ),
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.button("Desativar", type="button", variant="outline",
                                  color_scheme="red", size="2",
                                  disabled=AdminAvailabilityState.is_submitting)
                    ),
                    rx.dialog.content(
                        rx.dialog.title("Desativar horário"),
                        rx.dialog.description(
                            "Este horário deixará de aceitar novas reservas. "
                            "Consultas já reservadas não serão canceladas."
                        ),
                        rx.text(row["date_label"], " às ", row["time_label"],
                                font_weight="700", margin_y="1rem"),
                        rx.flex(
                            rx.dialog.close(
                                rx.button("Manter horário", type="button", variant="ghost")
                            ),
                            rx.dialog.close(
                                rx.button(
                                    "Confirmar desativação", type="button", color_scheme="red",
                                    on_click=AdminAvailabilityState.toggle_slot(row["id"], row["status"]),
                                    disabled=AdminAvailabilityState.is_submitting,
                                )
                            ),
                            justify="end", gap="2", flex_wrap="wrap",
                        ),
                        max_width="28rem",
                    ),
                ),
            ),
        ),
        justify="between", align="center", gap="3", width="100%",
        flex_wrap="wrap", class_name="vitta-calendar-slot-row",
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


def _weekday_select(*, control_id: str, value, on_change) -> rx.Component:
    return rx.select.root(
        rx.select.trigger(id=control_id, width="100%", class_name="vitta-select-trigger"),
        rx.select.content(
            rx.select.item("Segunda-feira", value="0"),
            rx.select.item("Terça-feira", value="1"),
            rx.select.item("Quarta-feira", value="2"),
            rx.select.item("Quinta-feira", value="3"),
            rx.select.item("Sexta-feira", value="4"),
            rx.select.item("Sábado", value="5"),
            rx.select.item("Domingo", value="6"),
            position="popper",
        ),
        value=value, on_change=on_change, size="3",
    )


def _admin_calendar_day(day) -> rx.Component:
    """Calendar cell: empty dates are inspectable, adjacent-month dates are not."""
    return rx.button(
        rx.vstack(
            rx.text(day["day"], font_weight="700", size="3"),
            rx.cond(
                day["has_slots"],
                rx.text(day["slot_count"], size="1",
                        class_name="vitta-calendar-day-count"),
                rx.fragment(),
            ),
            spacing="1", align="center", justify="center",
        ),
        type="button",
        class_name=rx.cond(
            day["is_selected"],
            "vitta-calendar-date is-selected",
            rx.cond(
                day["has_slots"],
                "vitta-calendar-date has-slots",
                rx.cond(
                    day["is_current_month"],
                    "vitta-calendar-date is-empty",
                    "vitta-calendar-date is-unavailable",
                ),
            ),
        ),
        disabled=~day["is_current_month"],
        on_click=AdminAvailabilityState.select_calendar_day(day["date_label"]),
        aria_label=day["aria_label"],
        aria_pressed=day["is_selected"],
        width="100%",
    )


def admin_calendar_view() -> rx.Component:
    """Compact month navigation and single-day drill-down, not a 500-row list."""
    return rx.vstack(
        rx.flex(
            rx.box(
                rx.heading("Disponibilidade dos médicos", size="4"),
                rx.text("Selecione qualquer data do mês para conferir disponibilidade ou ausência de horários.",
                        color="var(--vitta-text-muted)", size="2", margin_top="0.35rem"),
            ),
            rx.text("Somente horários persistidos, no fuso da clínica.",
                    size="2", color="var(--vitta-text-muted)"),
            direction=rx.breakpoints(initial="column", lg="row"),
            justify="between", align="center", gap="4", width="100%",
        ),
        rx.box(
            rx.flex(
                rx.button(rx.icon("chevron_left", size=19), type="button", variant="ghost",
                          on_click=AdminAvailabilityState.move_calendar_month(-1),
                          aria_label="Mês anterior", disabled=AdminAvailabilityState.is_loading),
                rx.heading(AdminAvailabilityState.calendar_month_title, size="4"),
                rx.button(rx.icon("chevron_right", size=19), type="button", variant="ghost",
                          on_click=AdminAvailabilityState.move_calendar_month(1),
                          aria_label="Próximo mês", disabled=AdminAvailabilityState.is_loading),
                align="center", justify="between", width="100%",
                class_name="vitta-calendar-header",
            ),
            rx.grid(
                *[rx.center(rx.text(name, size="2", font_weight="700"))
                  for name in ("Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb")],
                columns="7", gap="1", class_name="vitta-calendar-weekdays",
            ),
            rx.cond(
                AdminAvailabilityState.is_loading,
                rx.center(rx.spinner(size="3"), min_height="15rem", width="100%"),
                rx.grid(
                    rx.foreach(AdminAvailabilityState.calendar_days, _admin_calendar_day),
                    columns="7", gap="1", class_name="vitta-calendar-grid",
                ),
            ),
            class_name="vitta-availability-calendar",
        ),
        rx.cond(
            AdminAvailabilityState.selected_calendar_day != "",
            rx.vstack(
                rx.flex(
                    rx.heading(AdminAvailabilityState.selected_calendar_day, size="4"),
                    rx.hstack(
                        rx.text(AdminAvailabilityState.selected_day_available, " disponíveis", size="2"),
                        rx.text("·", color="var(--vitta-text-subtle)"),
                        rx.text(AdminAvailabilityState.selected_day_booked, " reservados", size="2"),
                        rx.text("·", color="var(--vitta-text-subtle)"),
                        rx.text(AdminAvailabilityState.selected_day_inactive, " inativos", size="2"),
                        spacing="2", flex_wrap="wrap", color="var(--vitta-text-muted)",
                    ),
                    justify="between", align="center", gap="3", width="100%", flex_wrap="wrap",
                ),
                rx.cond(
                    AdminAvailabilityState.selected_day_slots.length() > 0,
                    rx.vstack(
                        rx.foreach(AdminAvailabilityState.selected_day_slots, _admin_slot_row),
                        spacing="0", align="stretch", width="100%", role="list",
                    ),
                    rx.text("Não há horários cadastrados para esta data.",
                            color="var(--vitta-text-muted)", padding_y="1rem"),
                ),
                class_name="vitta-calendar-day-details",
                spacing="4", align="stretch", width="100%",
            ),
            rx.box(
                rx.icon("calendar_days", size=24, color="var(--vitta-text-subtle)"),
                rx.text("Escolha uma data do calendário para conferir os horários.",
                        color="var(--vitta-text-muted)", margin_top="0.6rem"),
                class_name="vitta-calendar-empty",
            ),
        ),
        spacing="5", align="stretch", width="100%",
    )


def admin_availability_panel() -> rx.Component:
    """Focused schedule management: each task has a separate accessible tab."""
    return section_panel(
        rx.vstack(
            rx.box(
                field_label("Médico responsável", "admin-schedule-professional"),
                _professional_select(
                    control_id="admin-schedule-professional",
                    value=AdminAvailabilityState.selected_professional,
                    on_change=AdminAvailabilityState.update_selected_professional,
                    include_all=False,
                    disabled=AdminAvailabilityState.is_loading | AdminAvailabilityState.is_submitting,
                ),
                width=rx.breakpoints(initial="100%", md="min(24rem, 100%)"),
            ),
            feedback_region(AdminAvailabilityState.error_message, AdminAvailabilityState.success_message,
                            "admin-hours-feedback"),
            rx.cond(
                AdminAvailabilityState.is_loading & ~AdminAvailabilityState.has_professionals,
                rx.center(rx.spinner(size="3"), min_height="10rem", width="100%"),
                rx.cond(
                    AdminAvailabilityState.has_professionals,
                    rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("Consultar disponibilidade", value="search"),
                    rx.tabs.trigger("Expediente semanal", value="weekly"),
                    rx.tabs.trigger("Horário avulso", value="single"),
                    class_name="vitta-task-tabs",
                ),
                rx.tabs.content(
                rx.el.form(
                    rx.vstack(
                        rx.heading("Expediente semanal do médico", size="4", color="var(--vitta-text)"),
                        rx.text("Configure os dias e o intervalo de trabalho. Horários de consulta disponíveis são publicados para os próximos 45 dias, sem cancelar reservas já existentes.", color="var(--vitta-text-muted)", size="2", line_height="1.5"),
                        rx.cond(
                            AdminAvailabilityState.weekly_existing,
                            rx.box(
                                rx.text("Expediente atualmente configurado", size="2", font_weight="700"),
                                rx.hstack(
                                    rx.text(AdminAvailabilityState.weekly_saved_summary,
                                            size="2", color="var(--vitta-text-muted)"),
                                    spacing="2", flex_wrap="wrap",
                                ),
                                class_name="vitta-info-strip",
                            ),
                            rx.text("Este médico ainda não possui expediente semanal.",
                                    color="var(--vitta-text-muted)", size="2"),
                        ),
                        rx.text("O período entre o primeiro e o último dia é contínuo. "
                                "A agenda atual aceita uma regra semanal por médico.",
                                color="var(--vitta-text-muted)", size="2"),
                        rx.grid(
                            rx.box(
                                field_label("Trabalha de", "admin-weekly-start-day"),
                                rx.box(_weekday_select(control_id="admin-weekly-start-day",
                                    value=AdminAvailabilityState.weekly_start_day,
                                    on_change=AdminAvailabilityState.update_weekly_start_day), margin_top="0.4rem"),
                            ),
                            rx.box(
                                field_label("Até", "admin-weekly-end-day"),
                                rx.box(_weekday_select(control_id="admin-weekly-end-day",
                                    value=AdminAvailabilityState.weekly_end_day,
                                    on_change=AdminAvailabilityState.update_weekly_end_day), margin_top="0.4rem"),
                            ),
                            rx.box(
                                field_label("Início do expediente", "admin-weekly-start-time"),
                                rx.el.input(id="admin-weekly-start-time", type="time", name="start_time",
                                            required=True, lang="pt-BR", class_name="vitta-input", margin_top="0.4rem",
                                            value=AdminAvailabilityState.weekly_start_time,
                                            on_change=AdminAvailabilityState.update_weekly_start_time),
                            ),
                            rx.box(
                                field_label("Fim do expediente", "admin-weekly-end-time"),
                                rx.el.input(id="admin-weekly-end-time", type="time", name="end_time",
                                            required=True, lang="pt-BR", class_name="vitta-input", margin_top="0.4rem",
                                            value=AdminAvailabilityState.weekly_end_time,
                                            on_change=AdminAvailabilityState.update_weekly_end_time),
                            ),
                            rx.box(
                                field_label("Duração da consulta", "admin-weekly-duration"),
                                rx.select.root(
                                    rx.select.trigger(id="admin-weekly-duration", width="100%", class_name="vitta-select-trigger"),
                                    rx.select.content(
                                        rx.select.item("30 minutos", value="30"),
                                        rx.select.item("60 minutos", value="60"),
                                        position="popper",
                                    ),
                                    value=AdminAvailabilityState.weekly_slot_minutes,
                                    on_change=AdminAvailabilityState.update_weekly_slot_minutes,
                                    size="3",
                                ),
                            ),
                            columns=rx.breakpoints(initial="1", sm="repeat(2, minmax(0, 1fr))", xl="repeat(5, minmax(0, 1fr))"),
                            gap="0.75rem", width="100%",
                        ),
                        rx.button(
                            rx.cond(AdminAvailabilityState.weekly_existing, "Salvar alterações do expediente", "Publicar expediente semanal"),
                            type="submit", color_scheme="teal", high_contrast=True,
                            disabled=AdminAvailabilityState.is_submitting | ~AdminAvailabilityState.has_professionals,
                            loading=AdminAvailabilityState.is_submitting, min_height="2.85rem",
                        ),
                        spacing="3", align="stretch", width="100%",
                    ),
                    on_submit=AdminAvailabilityState.save_weekly,
                    width="100%",
                ),
                    value="weekly",
                    padding_top="1.25rem",
                ),
                rx.tabs.content(
                rx.box(
                    rx.heading("Horário avulso", size="4", color="var(--vitta-text)"),
                    rx.text("Para encaixes ou exceções que não fazem parte do expediente semanal.", color="var(--vitta-text-muted)", size="2"),
                    width="100%",
                ),
                rx.el.form(
                    rx.grid(
                        rx.box(
                            field_label("Data do atendimento", "admin-slot-date"),
                            rx.el.input(
                                id="admin-slot-date",
                                name="date",
                                type="date",
                                lang="pt-BR",
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
                                lang="pt-BR",
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
                        columns=rx.breakpoints(initial="1", md="repeat(2, minmax(0, 1fr))", xl="minmax(9rem, 1fr) minmax(9rem, 1fr) auto"),
                        gap="0.75rem",
                        align_items="end",
                        width="100%",
                    ),
                    on_submit=AdminAvailabilityState.create_slot,
                    no_validate=False,
                    width="100%",
                ),
                    value="single",
                    padding_top="1.25rem",
                ),
                rx.tabs.content(
                    admin_calendar_view(),
                    value="search",
                    padding_top="1.25rem",
                ),
                value=AdminAvailabilityState.active_operation,
                on_change=AdminAvailabilityState.change_operation,
                width="100%",
                ),
                empty_state("stethoscope", "Nenhum médico ativo",
                            "Cadastre um profissional ativo antes de configurar horários."),
                ),
            ),
            spacing="4",
            align="stretch",
            width="100%",
        ),
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
            rx.vstack(
                _consultation_actions(row),
                rx.cond(
                    row["status"] != ConsultationStatus.CANCELADA.value,
                    rx.button(
                        rx.icon("calendar_plus", size=15),
                        "Adicionar ao calendário do paciente",
                        type="button", size="2",
                        variant="outline", color_scheme="teal",
                        on_click=ReceptionAgendaState.download_appointment_calendar(row["id"]),
                        disabled=ReceptionAgendaState.is_submitting,
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align=rx.breakpoints(initial="start", md="end"),
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


def reception_agenda_dialogs() -> rx.Component:
    """Shared appointment dialogs, mounted outside contextual menus."""
    return rx.fragment(_arrival_dialog(), _reschedule_dialog(), _cancel_dialog())


def reception_agenda_panel() -> rx.Component:
    """Paginated consultation results. Booking lives on its dedicated route."""
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.vstack(
                    rx.heading("Consultas agendadas", size="5"),
                    rx.text("Consulte e gerencie os agendamentos do período.",
                            color="var(--vitta-text-muted)", size="2"),
                    spacing="2", align="start",
                ),
                rx.link(
                    rx.hstack(rx.icon("calendar_plus", size=17),
                              rx.text("Nova consulta"), spacing="2", align="center"),
                    href="/recepcao/agenda/nova",
                    class_name="vitta-primary-action",
                ),
                justify="between", align="center", gap="4", flex_wrap="wrap", width="100%",
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
            rx.cond(
                ReceptionAgendaState.is_loading,
                rx.center(rx.spinner(size="3"), min_height="10rem", width="100%"),
                rx.cond(
                    ReceptionAgendaState.has_consultations,
                    rx.vstack(
                        rx.foreach(ReceptionAgendaState.paged_consultations, _consultation_row),
                        spacing="3", align="stretch", width="100%",
                    ),
                    empty_state(
                        "calendar_days", "Nenhuma consulta neste período",
                        "Ajuste os filtros ou cadastre uma nova consulta.",
                    ),
                ),
            ),
            rx.flex(
                rx.text("Página ", ReceptionAgendaState.consultation_page,
                        " de ", ReceptionAgendaState.consultation_total_pages,
                        color="var(--vitta-text-muted)", size="2"),
                rx.hstack(
                    rx.button("Anterior", variant="outline", color_scheme="teal",
                              on_click=ReceptionAgendaState.move_consultation_page(-1),
                              disabled=ReceptionAgendaState.consultation_page <= 1),
                    rx.button("Próxima", variant="outline", color_scheme="teal",
                              on_click=ReceptionAgendaState.move_consultation_page(1),
                              disabled=ReceptionAgendaState.consultation_page >= ReceptionAgendaState.consultation_total_pages),
                    spacing="3",
                ),
                justify="between", align="center", gap="3", flex_wrap="wrap", width="100%",
            ),
            reception_agenda_dialogs(),
            spacing="5", align="stretch", width="100%",
        ),
    )


def reception_booking_panel() -> rx.Component:
    """One task per screen: patient lookup, doctor/date filtering and slot booking."""
    return section_panel(
        rx.vstack(
            rx.heading("Dados do agendamento", size="4"),
            rx.text("Selecione um paciente e um horário realmente disponível.",
                    color="var(--vitta-text-muted)", size="2"),
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
                                    placeholder="000.000.000-00",
                                    required=True,
                                    max_length=14,
                                    min_length=14,
                                    pattern=r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}",
                                    title="Informe o CPF completo: 000.000.000-00",
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
                        rx.center(rx.spinner(size="3"), min_height="10rem", width="100%",
                                  role="status", aria_live="polite"),
                        rx.vstack(
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
                            spacing="3", align="stretch", width="100%",
                        ),
                    ),

            spacing="5", align="stretch", width="100%",
        ),
    )
