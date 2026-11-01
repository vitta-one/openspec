"""Calendário mensal compartilhado pela Administração e pelo preview QA."""

import reflex as rx


def _calendar_day(
    day,
    on_select_day,
    *,
    allow_empty: bool,
    show_consultations: bool,
    show_today: bool,
) -> rx.Component:
    markers = [
        rx.cond(
            day["has_slots"],
            rx.text(day["slot_count"], " horários", size="1", class_name="vitta-calendar-day-count"),
            rx.fragment(),
        )
    ]
    if show_consultations:
        markers.append(
            rx.cond(
                day["consultation_count"] > 0,
                rx.text(day["consultation_count"], " consultas", size="1", class_name="vitta-calendar-day-count"),
                rx.fragment(),
            )
        )
    selectable = day["is_current_month"] if allow_empty else day["has_slots"]
    extra_props = {}
    if show_today:
        extra_props["box_shadow"] = rx.cond(
            day["is_today"], "inset 0 0 0 2px var(--vitta-primary)", "none"
        )
    return rx.button(
        rx.vstack(
            rx.text(day["day"], font_weight="700", size="3"),
            *markers,
            spacing="1", align="center", justify="center",
        ),
        type="button",
        class_name=rx.cond(
            day["is_selected"],
            "vitta-calendar-date is-selected",
            rx.cond(
                day["has_slots"],
                "vitta-calendar-date has-slots",
                "vitta-calendar-date is-unavailable",
            ),
        ),
        disabled=~selectable,
        on_click=on_select_day(day["date_label"]),
        aria_label=day["aria_label"],
        aria_pressed=day["is_selected"],
        width="100%",
        **extra_props,
    )


def month_calendar(
    *,
    month_title,
    days,
    is_loading,
    on_previous,
    on_next,
    on_select_day,
    allow_empty: bool = False,
    show_consultations: bool = False,
    show_today: bool = False,
) -> rx.Component:
    """One accessible calendar primitive; read-only mode changes only event handlers."""
    return rx.box(
        rx.flex(
            rx.button(
                rx.icon("chevron_left", size=19),
                type="button",
                variant="ghost",
                on_click=on_previous,
                aria_label="Mês anterior",
                disabled=is_loading,
            ),
            rx.heading(month_title, size="4"),
            rx.button(
                rx.icon("chevron_right", size=19),
                type="button",
                variant="ghost",
                on_click=on_next,
                aria_label="Próximo mês",
                disabled=is_loading,
            ),
            align="center", justify="between", width="100%",
            class_name="vitta-calendar-header",
        ),
        rx.grid(
            *[
                rx.center(rx.text(name, size="2", font_weight="700"))
                for name in ("Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb")
            ],
            columns="7", gap="1", class_name="vitta-calendar-weekdays",
        ),
        rx.cond(
            is_loading,
            rx.center(rx.spinner(size="3"), min_height="15rem", width="100%"),
            rx.grid(
                rx.foreach(
                    days,
                    lambda day: _calendar_day(
                        day,
                        on_select_day,
                        allow_empty=allow_empty,
                        show_consultations=show_consultations,
                        show_today=show_today,
                    ),
                ),
                columns="7", gap="1", class_name="vitta-calendar-grid",
            ),
        ),
        class_name="vitta-availability-calendar",
    )
