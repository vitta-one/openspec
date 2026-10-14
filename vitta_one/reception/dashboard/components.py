"""Operational home for a receptionist; all values are real SQL projections."""
import reflex as rx

from vitta_one.reception.dashboard.state import ReceptionDashboardState as S
from vitta_one.ui.components import empty_state, page_header, section_panel


def _kpi(label: str, value, detail: str, href: str, icon: str) -> rx.Component:
    return rx.link(
        rx.box(
            rx.hstack(
                rx.text(label, font_weight="650", size="2", color="var(--vitta-text-muted)"),
                rx.icon(icon, size=17, color="var(--vitta-primary)"),
                justify="between", align="center", width="100%",
            ),
            rx.heading(value, size="8", margin_top="0.65rem", font_family="var(--vitta-font-display)"),
            rx.text(detail, size="1", color="var(--vitta-text-subtle)", margin_top="0.25rem"),
            class_name="vitta-metric-card",
            width="100%",
        ),
        href=href, aria_label=label + ": abrir módulo",
        class_name="vitta-reception-kpi-link",
    )


def _next_consultation(row) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(row["patient"], font_weight="700", size="2"),
            rx.text(row["professional"], color="var(--vitta-text-muted)", size="2"),
            min_width="0", flex="1",
        ),
        rx.box(rx.text(row["when"], size="2", class_name="vitta-tabular"),
               color="var(--vitta-text-muted)"),
        align="center", justify="between", gap="3",
        width="100%", class_name="vitta-data-row", role="listitem",
    )


def reception_dashboard() -> rx.Component:
    return rx.vstack(
        page_header(
            "Central operacional",
            "Visão geral da Recepção",
            "Agenda de hoje, fila ativa e próximos atendimentos — dados atualizados a partir do banco da clínica.",
            rx.button(
                rx.icon("refresh_cw", size=16), "Atualizar",
                on_click=S.load, variant="outline", color_scheme="teal",
                loading=S.is_loading, disabled=S.is_loading,
            ),
        ),
        rx.hstack(
            rx.link("Cadastrar paciente", href="/recepcao/pacientes",
                    class_name="vitta-context-link"),
            rx.link("Agendar consulta", href="/recepcao/agenda",
                    class_name="vitta-context-link"),
            rx.link("Abrir fila", href="/recepcao/fila",
                    class_name="vitta-context-link"),
            flex_wrap="wrap", gap="2", width="100%",
        ),
        rx.cond(
            S.error_message != "",
            rx.callout(S.error_message, icon="alert_triangle", color_scheme="red", role="alert"),
            rx.fragment(),
        ),
        rx.cond(
            S.is_loading,
            rx.hstack(rx.spinner(size="2"), rx.text("Atualizando informações da clínica…"),
                      role="status", align="center", width="100%"),
            rx.fragment(),
        ),
        rx.cond(
            S.last_updated != "",
            rx.text("Dia da clínica: ", S.clinic_day, " · Atualizado em ", S.last_updated,
                    size="1", color="var(--vitta-text-subtle)"),
            rx.fragment(),
        ),
        rx.grid(
            _kpi("Agendamentos de hoje", S.scheduled_today,
                 "Consultas do dia, exceto canceladas", "/recepcao/agenda", "calendar_days"),
            _kpi("Aguardando", S.waiting,
                 "Entradas na fila, todas as datas", "/recepcao/fila", "users"),
            _kpi("Em atendimento", S.attending,
                 "Entradas em atendimento agora", "/recepcao/fila", "stethoscope"),
            _kpi("Finalizados hoje", S.finished_today,
                 "Entradas concluídas no dia clínico", "/recepcao/fila", "check_circle"),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            gap="3", width="100%",
        ),
        rx.grid(
            section_panel(
                rx.hstack(
                    rx.heading("Próximas consultas", size="5"),
                    rx.link("Ver agenda", href="/recepcao/agenda",
                            class_name="vitta-context-link"),
                    justify="between", align="center", width="100%", flex_wrap="wrap",
                ),
                rx.cond(
                    S.next_consultations.length() > 0,
                    rx.vstack(rx.foreach(S.next_consultations, _next_consultation),
                              align="stretch", spacing="2", width="100%", role="list"),
                    empty_state("calendar_clock", "Sem próximas consultas",
                                "Não há consultas futuras agendadas neste momento."),
                ),
            ),
            section_panel(
                rx.heading("Situação da fila", size="5"),
                rx.vstack(
                    rx.hstack(rx.text("Prioridade vermelha"), rx.spacer(),
                              rx.badge(S.waiting_red, color_scheme="red"), width="100%"),
                    rx.hstack(rx.text("Prioridade amarela"), rx.spacer(),
                              rx.badge(S.waiting_yellow, color_scheme="amber"), width="100%"),
                    rx.hstack(rx.text("Prioridade verde"), rx.spacer(),
                              rx.badge(S.waiting_green, color_scheme="green"), width="100%"),
                    spacing="4", align="stretch", width="100%",
                ),
                rx.text("A prioridade é informada pela operação; o tempo de espera não altera a classificação.",
                        size="1", color="var(--vitta-text-muted)"),
            ),
            columns=rx.breakpoints(initial="1", lg="2"), gap="3", width="100%",
        ),
        section_panel(
            rx.heading("Acompanhamento do dia", size="5"),
            rx.hstack(
                rx.badge("Chegadas confirmadas hoje: ", S.confirmed_today, variant="soft"),
                rx.badge("Agendamentos com horário passado sem chegada: ",
                         S.arrivals_pending, variant="soft", color_scheme="amber"),
                flex_wrap="wrap", gap="3", width="100%",
            ),
            rx.text("Horário passado não equivale a falta ou urgência médica.",
                    size="1", color="var(--vitta-text-muted)"),
        ),
        align="stretch", width="100%", spacing="4",
    )
