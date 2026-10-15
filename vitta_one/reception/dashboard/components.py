"""Operational home for a receptionist; all values are real SQL projections."""
import reflex as rx

from vitta_one.reception.dashboard.state import ReceptionDashboardState as S
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
                ),
                rx.icon(icon, size=17, color="var(--vitta-primary)"),
                justify="between",
                align="center",
                width="100%",
            ),
            rx.heading(
                value,
                size="8",
                margin_top="0.65rem",
                font_family="var(--vitta-font-display)",
            ),
            rx.text(
                detail,
                size="1",
                color="var(--vitta-text-subtle)",
                margin_top="0.25rem",
            ),
            class_name="vitta-metric-card",
            width="100%",
        ),
        href=href,
        aria_label=f"{label}: abrir seção",
        class_name="vitta-reception-kpi-link",
    )


def _next_consultation(row) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.hstack(
                rx.text(
                    row["when"],
                    size="2",
                    font_weight="700",
                    class_name="vitta-tabular",
                ),
                rx.badge(row["status"], color_scheme="teal", variant="soft"),
                align="center",
                flex_wrap="wrap",
                gap="2",
            ),
            rx.text(row["patient"], font_weight="700", size="2", margin_top="1"),
            rx.text(
                "Profissional: ",
                row["professional"],
                color="var(--vitta-text-muted)",
                size="2",
            ),
            min_width="0",
            flex="1",
        ),
        rx.link(
            "Ver na agenda",
            href="/recepcao/agenda",
            class_name="vitta-context-link",
        ),
        align="center",
        justify="between",
        gap="3",
        width="100%",
        class_name="vitta-data-row",
        role="listitem",
        flex_wrap="wrap",
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
        class_name="vitta-data-row",
        role="listitem",
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
            rx.badge("Dia da clínica: ", S.clinic_day, variant="soft"),
            rx.text(
                "Última leitura bem-sucedida: ",
                S.last_updated,
                size="1",
                color="var(--vitta-text-subtle)",
            ),
            align="center",
            flex_wrap="wrap",
            gap="3",
            width="100%",
        ),
        rx.grid(
            _kpi(
                "Consultas hoje",
                S.scheduled_today,
                "Consultas do dia, exceto canceladas",
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
            columns=rx.breakpoints(initial="1", sm="2", lg="3"),
            gap="3",
            width="100%",
        ),
        rx.grid(
            section_panel(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Próximas consultas", size="5"),
                        rx.link(
                            "Abrir agenda",
                            href="/recepcao/agenda",
                            class_name="vitta-context-link",
                        ),
                        justify="between",
                        align="center",
                        flex_wrap="wrap",
                        width="100%",
                    ),
                    rx.text(
                        "Consultas futuras agendadas, em ordem de horário.",
                        size="1",
                        color="var(--vitta-text-muted)",
                    ),
                    rx.cond(
                        S.next_consultations.length() > 0,
                        rx.vstack(
                            rx.foreach(S.next_consultations, _next_consultation),
                            align="stretch",
                            spacing="2",
                            width="100%",
                            role="list",
                        ),
                        empty_state(
                            "calendar_clock",
                            "Sem próximas consultas",
                            "Não há consultas futuras agendadas neste momento.",
                        ),
                    ),
                    align="stretch",
                    spacing="3",
                    width="100%",
                )
            ),
            section_panel(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Situação da fila", size="5"),
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
                        spacing="4",
                        align="stretch",
                        width="100%",
                    ),
                    rx.text(
                        "A prioridade é informada pela operação; o tempo de espera não altera a classificação.",
                        size="1",
                        color="var(--vitta-text-muted)",
                    ),
                    align="stretch",
                    spacing="3",
                    width="100%",
                )
            ),
            columns=rx.breakpoints(initial="1", lg="2"),
            gap="3",
            width="100%",
            align_items="stretch",
        ),
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
                    ),
                ),
                align="stretch",
                spacing="3",
                width="100%",
            )
        ),
    )


def reception_dashboard() -> rx.Component:
    return rx.vstack(
        page_header(
            "Recepção",
            "Central operacional",
            "Acompanhe a agenda, a fila e as pendências do dia com dados da clínica.",
            rx.button(
                rx.icon("plus", size=16),
                "Agendar consulta",
                on_click=rx.redirect("/recepcao/agenda"),
                color_scheme="teal",
                class_name="vitta-primary-action",
            ),
            rx.link(
                "Cadastrar paciente",
                href="/recepcao/pacientes",
                class_name="vitta-context-link",
            ),
            rx.button(
                rx.icon("refresh_cw", size=16),
                "Atualizar",
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
                    on_click=S.load,
                    variant="outline",
                    color_scheme="teal",
                    loading=S.is_loading,
                    disabled=S.is_loading,
                ),
                align="start",
                width="100%",
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
                    padding="1rem",
                ),
                rx.fragment(),
            ),
        ),
        align="stretch",
        width="100%",
        spacing="4",
    )
