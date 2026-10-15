"""Operational home for a receptionist; all values are real SQL projections."""
import reflex as rx

from vitta_one.reception.dashboard.state import ReceptionDashboardState as S
from vitta_one.ui.appointment_components import consultation_status_badge
from vitta_one.ui.components import empty_state, page_header, section_panel


def _kpi(label: str, value, detail: str, href: str, icon: str) -> rx.Component:
    return rx.link(
        rx.box(
            rx.hstack(
                rx.text(
                    label,
                    font_weight="650",
                    size="2",
                    color="var(--vitta-text-muted)",
                    line_height="1.35",
                    min_width="0",
                ),
                rx.icon(icon, size=18, color="var(--vitta-primary)"),
                justify="between",
                align="start",
                gap="2",
                width="100%",
            ),
            rx.text(
                value,
                font_size="2rem",
                font_weight="800",
                line_height="1",
                letter_spacing="-0.04em",
                font_family="var(--vitta-font-display)",
                class_name="vitta-tabular vitta-reception-kpi-value",
                margin_top="0.75rem",
            ),
            rx.text(
                detail,
                size="1",
                color="var(--vitta-text-subtle)",
                line_height="1.45",
                margin_top="0.5rem",
            ),
            class_name="vitta-metric-card vitta-reception-kpi",
            width="100%",
        ),
        href=href,
        aria_label=f"{label}: abrir seção",
        class_name="vitta-reception-kpi-link",
    )


def _calendar_status(row) -> rx.Component:
    return rx.cond(
        row["is_pending"] == "true",
        rx.badge(
            row["status"],
            color_scheme="amber",
            variant="soft",
            high_contrast=True,
            class_name="vitta-reception-calendar-status",
        ),
        consultation_status_badge(
            row["status_value"],
            row["status"],
            class_name="vitta-reception-calendar-status",
        ),
    )

def _calendar_event(row) -> rx.Component:
    return rx.box(
        rx.text(
            row["time"],
            font_weight="800",
            class_name="vitta-tabular vitta-reception-calendar-time",
        ),
        rx.box(
            rx.text(
                row["patient"],
                font_weight="700",
                size="2",
                line_height="1.35",
                overflow_wrap="anywhere",
            ),
            rx.text(
                "Profissional: ",
                row["professional"],
                size="1",
                color="var(--vitta-text-muted)",
                line_height="1.4",
                margin_top="0.25rem",
                overflow_wrap="anywhere",
            ),
            min_width="0",
            class_name="vitta-reception-calendar-details",
        ),
        _calendar_status(row),
        class_name="vitta-reception-calendar-event",
        role="listitem",
    )


def _calendar_day(day) -> rx.Component:
    return rx.button(
        rx.vstack(
            rx.hstack(
                rx.text(
                    day["weekday_label"],
                    font_size="0.78rem",
                    font_weight="700",
                    text_transform="capitalize",
                    color="var(--vitta-text-muted)",
                ),
                align="center",
                justify="between",
                width="100%",
                gap="1",
            ),
            rx.text(
                day["day_number"],
                font_size="1.55rem",
                font_weight="800",
                line_height="1",
                font_family="var(--vitta-font-display)",
                class_name="vitta-tabular vitta-reception-calendar-day-number",
            ),
            rx.text(
                day["count_label"],
                font_size="0.75rem",
                font_weight="650",
                color="var(--vitta-text-muted)",
                line_height="1.35",
            ),
            rx.cond(
                day["cancelled_label"] != "",
                rx.text(
                    day["cancelled_label"],
                    font_size="0.7rem",
                    color="var(--vitta-text-subtle)",
                    line_height="1.3",
                ),
                rx.fragment(),
            ),
            align="stretch",
            spacing="2",
            width="100%",
        ),
        type="button",
        variant="outline",
        size="3",
        on_click=S.select_calendar_day(day["date"]),
        class_name=rx.cond(
            day["date"] == S.selected_calendar_date,
            "vitta-reception-calendar-day is-selected",
            rx.cond(
                day["is_today"] == "true",
                "vitta-reception-calendar-day is-today",
                "vitta-reception-calendar-day",
            ),
        ),
        aria_label=day["aria_label"],
        aria_pressed=day["date"] == S.selected_calendar_date,
        width="100%",
    )


def _calendar_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.heading("Agenda dos próximos 7 dias", size="5"),
                    rx.text(
                        "Os números contam consultas não canceladas; canceladas aparecem separadamente.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        line_height="1.5",
                        margin_top="0.5rem",
                    ),
                    min_width="0",
                ),
                rx.vstack(
                    rx.text(
                        S.calendar_range,
                        font_weight="700",
                        class_name="vitta-tabular",
                    ),
                    rx.link(
                        "Abrir agenda completa",
                        href="/recepcao/agenda",
                        class_name="vitta-context-link",
                    ),
                    align=rx.breakpoints(initial="start", sm="end"),
                    spacing="1",
                    min_width="0",
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                justify="between",
                align=rx.breakpoints(initial="stretch", sm="center"),
                gap="1rem",
                width="100%",
            ),
            rx.text(
                "Deslize para ver os sete dias.",
                size="1",
                color="var(--vitta-text-subtle)",
                class_name="vitta-reception-calendar-scroll-hint",
            ),
            rx.box(
                rx.foreach(S.calendar_days, _calendar_day),
                width="100%",
                class_name="vitta-reception-calendar-days",
                role="group",
                aria_label="Dias disponíveis na agenda",
            ),
            rx.box(
                rx.flex(
                    rx.box(
                        rx.heading(S.selected_calendar_label, size="4"),
                        rx.text(
                            S.selected_calendar_summary,
                            size="1",
                            color="var(--vitta-text-subtle)",
                            margin_top="0.25rem",
                            role="status",
                            aria_live="polite",
                        ),
                        min_width="0",
                    ),
                    rx.link(
                        "Revisar no módulo Agenda",
                        href="/recepcao/agenda",
                        class_name="vitta-context-link",
                    ),
                    direction=rx.breakpoints(initial="column", sm="row"),
                    justify="between",
                    align=rx.breakpoints(initial="start", sm="center"),
                    gap="0.75rem",
                    width="100%",
                ),
                rx.cond(
                    S.selected_calendar_consultations.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            S.selected_calendar_consultations,
                            _calendar_event,
                        ),
                        align="stretch",
                        spacing="0",
                        width="100%",
                        role="list",
                        margin_top="1rem",
                    ),
                    empty_state(
                        "calendar",
                        "Nenhuma consulta neste dia",
                        "A agenda não tem consultas registradas para esta data.",
                        min_height="7rem",
                        padding="1rem",
                    ),
                ),
                class_name="vitta-reception-calendar-selected-day",
            ),
            spacing="5",
            align="stretch",
            width="100%",
        ),
        padding=rx.breakpoints(initial="1.25rem", sm="1.5rem", lg="1.75rem"),
        class_name="vitta-reception-calendar-panel",
    )


def _pending_arrival(row) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(row["patient"], font_weight="700", size="2"),
            rx.text(
                "Profissional: ",
                row["professional"],
                color="var(--vitta-text-muted)",
                size="2",
            ),
            rx.text(
                "Horário: ",
                row["when"],
                color="var(--vitta-text-muted)",
                size="1",
                class_name="vitta-tabular",
            ),
            min_width="0",
            flex="1",
        ),
        rx.link(
            "Revisar na agenda",
            href="/recepcao/agenda",
            class_name="vitta-context-link",
        ),
        align="center",
        justify="between",
        gap="3",
        width="100%",
        class_name="vitta-data-row vitta-reception-list-row",
        role="listitem",
        flex_wrap="wrap",
    )


def _dashboard_content() -> rx.Component:
    return rx.fragment(
        rx.cond(
            S.is_loading,
            rx.callout(
                "Atualizando os dados. A última leitura permanece identificada abaixo.",
                icon="refresh_cw",
                color_scheme="teal",
                role="status",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.badge(
                "Dia da clínica: ",
                S.clinic_day,
                variant="soft",
                class_name="vitta-reception-day-badge",
            ),
            rx.text(
                "Última leitura bem-sucedida: ",
                S.last_updated,
                size="1",
                color="var(--vitta-text-subtle)",
                class_name="vitta-reception-updated",
            ),
            align="center",
            flex_wrap="wrap",
            gap="3",
            width="100%",
            class_name="vitta-reception-metadata",
        ),
        _calendar_panel(),
        rx.grid(
            section_panel(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Precisa da sua atenção", size="5"),
                        rx.badge(
                            S.arrivals_pending,
                            " pendências de chegada",
                            color_scheme="amber",
                            variant="soft",
                        ),
                        align="center",
                        flex_wrap="wrap",
                        gap="2",
                    ),
                    rx.text(
                        "Consultas de hoje com horário ultrapassado e chegada ainda não confirmada. "
                        "Isso não classifica ausência nem urgência.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        line_height="1.5",
                    ),
                    rx.cond(
                        S.arrivals_pending > 0,
                        rx.vstack(
                            rx.foreach(S.pending_arrivals, _pending_arrival),
                            rx.cond(
                                S.arrivals_pending > S.pending_arrivals.length(),
                                rx.text(
                                    "Exibindo as 5 primeiras de ",
                                    S.arrivals_pending,
                                    " pendências.",
                                    size="1",
                                    color="var(--vitta-text-subtle)",
                                ),
                                rx.fragment(),
                            ),
                            align="stretch",
                            spacing="2",
                            width="100%",
                            role="list",
                        ),
                        empty_state(
                            "check_circle",
                            "Nenhuma pendência de chegada",
                            "Não há consultas de hoje com horário ultrapassado aguardando revisão.",
                            min_height="7.5rem",
                            padding="1.25rem",
                        ),
                    ),
                    align="stretch",
                    spacing="4",
                    width="100%",
                ),
                padding=rx.breakpoints(initial="1.25rem", sm="1.5rem", lg="1.75rem"),
            ),
            section_panel(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Fila por prioridade", size="5"),
                        rx.link(
                            "Abrir fila",
                            href="/recepcao/fila",
                            class_name="vitta-context-link",
                        ),
                        justify="between",
                        align="center",
                        flex_wrap="wrap",
                        width="100%",
                    ),
                    rx.text(
                        "Aguardando por prioridade informada",
                        font_weight="700",
                        size="2",
                        margin_top="0.25rem",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.text("Prioridade vermelha"),
                            rx.spacer(),
                            rx.badge(S.waiting_red, color_scheme="red"),
                            width="100%",
                        ),
                        rx.hstack(
                            rx.text("Prioridade amarela"),
                            rx.spacer(),
                            rx.badge(S.waiting_yellow, color_scheme="amber"),
                            width="100%",
                        ),
                        rx.hstack(
                            rx.text("Prioridade verde"),
                            rx.spacer(),
                            rx.badge(S.waiting_green, color_scheme="green"),
                            width="100%",
                        ),
                        spacing="3",
                        align="stretch",
                        width="100%",
                    ),
                    rx.text(
                        "A prioridade é informada pela operação; o tempo de espera não altera a classificação.",
                        size="1",
                        color="var(--vitta-text-muted)",
                        line_height="1.5",
                    ),
                    align="stretch",
                    spacing="4",
                    width="100%",
                ),
                padding=rx.breakpoints(initial="1.25rem", sm="1.5rem", lg="1.75rem"),
            ),
            columns=rx.breakpoints(initial="1", md="minmax(0, 1.35fr) minmax(18rem, 0.85fr)"),
            gap="4",
            width="100%",
            align_items="stretch",
        ),
        rx.vstack(
            rx.box(
                rx.heading("Resumo da recepção", size="5"),
                rx.text(
                    "Indicadores do dia clínico e da fila atual.",
                    size="2",
                    color="var(--vitta-text-muted)",
                    margin_top="0.5rem",
                ),
            ),
            rx.grid(
                _kpi(
                    "Consultas hoje",
                    S.scheduled_today,
                    "Não canceladas no dia clínico",
                    "/recepcao/agenda",
                    "calendar_days",
                ),
                _kpi(
                    "Chegadas confirmadas",
                    S.confirmed_today,
                    "Consultas de hoje confirmadas",
                    "/recepcao/agenda",
                    "check_circle",
                ),
                _kpi(
                    "Pendências de chegada",
                    S.arrivals_pending,
                    "Horário passou hoje; sem confirmação",
                    "/recepcao/agenda",
                    "alarm_clock",
                ),
                _kpi(
                    "Aguardando",
                    S.waiting,
                    "Entradas que aguardam atendimento",
                    "/recepcao/fila",
                    "users",
                ),
                _kpi(
                    "Em atendimento",
                    S.attending,
                    "Entradas em atendimento agora",
                    "/recepcao/fila",
                    "stethoscope",
                ),
                _kpi(
                    "Finalizados hoje",
                    S.finished_today,
                    "Entradas concluídas no dia clínico",
                    "/recepcao/fila",
                    "check_circle",
                ),
                columns=rx.breakpoints(initial="2", sm="3", lg="3"),
                gap="4",
                width="100%",
            ),
            align="stretch",
            spacing="4",
            width="100%",
        ),
    )


def reception_dashboard() -> rx.Component:
    return rx.vstack(
        page_header(
            "Recepção",
            "Central operacional",
            "Organize os horários do dia, confirme chegadas na Agenda e acompanhe a fila da clínica.",
            rx.button(
                rx.icon("plus", size=16),
                "Agendar consulta",
                type="button",
                on_click=rx.redirect("/recepcao/agenda"),
                color_scheme="teal",
                class_name="vitta-primary-action",
            ),
            rx.link(
                "Localizar paciente",
                href="/recepcao/pacientes",
                class_name="vitta-context-link",
            ),
            rx.button(
                rx.icon("refresh_cw", size=16),
                "Atualizar",
                type="button",
                on_click=S.load,
                variant="outline",
                color_scheme="teal",
                loading=S.is_loading,
                disabled=S.is_loading,
            ),
        ),
        rx.cond(
            S.error_message != "",
            rx.vstack(
                rx.callout(
                    S.error_message,
                    icon="alert_triangle",
                    color_scheme="red",
                    role="alert",
                ),
                rx.button(
                    "Tentar novamente",
                    type="button",
                    on_click=S.load,
                    variant="outline",
                    color_scheme="teal",
                    loading=S.is_loading,
                    disabled=S.is_loading,
                ),
                align="start",
                width="100%",
                spacing="3",
            ),
            rx.fragment(),
        ),
        rx.cond(
            S.has_loaded,
            _dashboard_content(),
            rx.cond(
                S.error_message == "",
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text("Carregando o painel com dados da clínica…"),
                    role="status",
                    align="center",
                    width="100%",
                    padding="1.25rem",
                    class_name="vitta-reception-initial-loading",
                ),
                rx.fragment(),
            ),
        ),
        align="stretch",
        width="100%",
        spacing="6",
    )
