"""Reusable UI for the patient reception queue capability."""

import reflex as rx

from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState
from vitta_one.ui.components import error_banner


def section_panel(*children, **props) -> rx.Component:
    """Render a quiet operational section using the established Vitta-One surface."""
    return rx.box(
        *children,
        width="100%",
        padding=rx.breakpoints(initial="1rem", sm="1.35rem"),
        background="var(--vitta-surface)",
        border="1px solid var(--vitta-border)",
        border_radius="var(--vitta-radius-panel)",
        **props,
    )


def success_banner(message) -> rx.Component:
    return rx.box(
        rx.text(message, size="2", line_height="1.5"),
        width="100%",
        padding="0.8rem 0.9rem",
        border="1px solid var(--vitta-success-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-success-soft)",
        color="var(--vitta-success)",
        role="status",
        aria_live="polite",
    )


def feedback_region(error, success) -> rx.Component:
    return rx.box(
        rx.cond(error != "", error_banner(error, "queue-feedback"), rx.fragment()),
        rx.cond(success != "", success_banner(success), rx.fragment()),
        width="100%",
    )


def field_label(text: str, control_id: str) -> rx.Component:
    return rx.el.label(
        text,
        html_for=control_id,
        font_weight="650",
        font_size="0.9rem",
        color="var(--vitta-text)",
    )


def priority_select(
    *,
    name: str,
    control_id: str,
    value=None,
    on_change=None,
    default_value: str | None = None,
    disabled=False,
) -> rx.Component:
    """Use the maintained Radix select with domain values and human labels."""
    root_props = {
        "name": name,
        "required": True,
        "disabled": disabled,
        "size": "3",
    }
    if value is not None:
        root_props["value"] = value
    if on_change is not None:
        root_props["on_change"] = on_change
    if default_value is not None:
        root_props["default_value"] = default_value

    return rx.select.root(
        rx.select.trigger(
            id=control_id,
            placeholder="Selecione a prioridade",
            width="100%",
            class_name="vitta-select-trigger",
            aria_describedby="priority-help",
        ),
        rx.select.content(
            rx.select.item("Vermelho", value="VERMELHO"),
            rx.select.item("Amarelo", value="AMARELO"),
            rx.select.item("Verde", value="VERDE"),
            position="popper",
        ),
        **root_props,
    )


def priority_badge(priority, label) -> rx.Component:
    return rx.match(
        priority,
        (
            "VERMELHO",
            rx.badge(label, color_scheme="red", high_contrast=True, variant="soft"),
        ),
        (
            "AMARELO",
            rx.badge(label, color_scheme="amber", high_contrast=True, variant="soft"),
        ),
        (
            "VERDE",
            rx.badge(label, color_scheme="green", high_contrast=True, variant="soft"),
        ),
        rx.badge(label, color_scheme="gray", high_contrast=True, variant="soft"),
    )


def patient_selection_summary() -> rx.Component:
    return rx.cond(
        ReceptionQueueState.selected_patient_id > 0,
        rx.flex(
            rx.box(
                rx.text("Paciente selecionado", size="1", color="var(--vitta-text-muted)"),
                rx.text(
                    ReceptionQueueState.selected_patient_name,
                    font_weight="700",
                    color="var(--vitta-text)",
                ),
            ),
            rx.button(
                "Limpar seleção",
                type="button",
                variant="ghost",
                color_scheme="teal",
                on_click=ReceptionQueueState.clear_patient_selection,
            ),
            width="100%",
            direction=rx.breakpoints(initial="column", sm="row"),
            align=rx.breakpoints(initial="stretch", sm="center"),
            justify="between",
            gap="0.75rem",
            padding="0.9rem 1rem",
            background="var(--vitta-primary-soft)",
            border_radius="var(--vitta-radius-control)",
        ),
        rx.box(
            rx.text(
                "Localize ou cadastre um paciente para habilitar a entrada na fila.",
                size="2",
                color="var(--vitta-text-muted)",
                line_height="1.5",
            ),
            width="100%",
            padding="0.9rem 1rem",
            background="var(--vitta-surface-muted)",
            border_radius="var(--vitta-radius-control)",
        ),
    )


def patient_identity_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.box(
                rx.heading("Paciente", size="5"),
                rx.text(
                    "Localize um cadastro existente pelo CPF ou crie um novo antes de registrar a entrada.",
                    color="var(--vitta-text-muted)",
                    size="2",
                    line_height="1.55",
                    margin_top="0.35rem",
                ),
                width="100%",
            ),
            rx.flex(
                rx.el.form(
                    rx.vstack(
                        rx.heading("Localizar", size="3"),
                        rx.box(
                            field_label("CPF", "patient-search-cpf"),
                            rx.el.input(
                                id="patient-search-cpf",
                                name="cpf",
                                type="text",
                                input_mode="numeric",
                                auto_complete="off",
                                required=True,
                                max_length=14,
                                class_name="vitta-input",
                                placeholder="000.000.000-00",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.button(
                            "Localizar paciente",
                            type="submit",
                            width="100%",
                            min_height="2.75rem",
                            variant="outline",
                            color_scheme="teal",
                            disabled=ReceptionQueueState.is_submitting,
                            loading=ReceptionQueueState.is_submitting,
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    on_submit=ReceptionQueueState.find_patient,
                    width="100%",
                ),
                rx.el.form(
                    rx.vstack(
                        rx.heading("Novo cadastro", size="3"),
                        rx.box(
                            field_label("Nome completo", "patient-create-name"),
                            rx.el.input(
                                id="patient-create-name",
                                name="name",
                                type="text",
                                auto_complete="name",
                                required=True,
                                max_length=160,
                                class_name="vitta-input",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.box(
                            field_label("CPF", "patient-create-cpf"),
                            rx.el.input(
                                id="patient-create-cpf",
                                name="cpf",
                                type="text",
                                input_mode="numeric",
                                auto_complete="off",
                                required=True,
                                max_length=14,
                                class_name="vitta-input",
                                placeholder="000.000.000-00",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.button(
                            "Cadastrar paciente",
                            type="submit",
                            width="100%",
                            min_height="2.75rem",
                            color_scheme="teal",
                            high_contrast=True,
                            disabled=ReceptionQueueState.is_submitting,
                            loading=ReceptionQueueState.is_submitting,
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    on_submit=ReceptionQueueState.create_patient,
                    width="100%",
                ),
                direction=rx.breakpoints(initial="column", lg="row"),
                gap="1.25rem",
                align="start",
                width="100%",
            ),
            patient_selection_summary(),
            spacing="5",
            width="100%",
            align="stretch",
        )
    )


def enqueue_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.box(
                rx.heading("Entrada na fila", size="5"),
                rx.text(
                    "Registre o relato recebido e selecione a prioridade informada pela operação. O Vitta-One não calcula gravidade clínica.",
                    color="var(--vitta-text-muted)",
                    size="2",
                    line_height="1.55",
                    margin_top="0.35rem",
                ),
                width="100%",
            ),
            rx.cond(
                ReceptionQueueState.selected_patient_id > 0,
                rx.el.form(
                    rx.vstack(
                        rx.box(
                            field_label("Sintomas relatados", "queue-symptoms"),
                            rx.el.textarea(
                                id="queue-symptoms",
                                name="symptoms",
                                required=True,
                                max_length=4000,
                                rows=4,
                                class_name="vitta-textarea",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.box(
                            field_label("Prioridade informada", "queue-priority"),
                            priority_select(
                                name="priority",
                                control_id="queue-priority",
                                default_value="VERDE",
                                disabled=ReceptionQueueState.is_submitting,
                            ),
                            rx.text(
                                "Escolha exatamente a classificação recebida: Vermelho, Amarelo ou Verde.",
                                id="priority-help",
                                size="1",
                                color="var(--vitta-text-muted)",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.button(
                            "Adicionar à fila",
                            type="submit",
                            min_height="3rem",
                            width="100%",
                            color_scheme="teal",
                            high_contrast=True,
                            disabled=ReceptionQueueState.is_submitting,
                            loading=ReceptionQueueState.is_submitting,
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    on_submit=ReceptionQueueState.enqueue,
                    width="100%",
                ),
                patient_selection_summary(),
            ),
            spacing="5",
            width="100%",
            align="stretch",
        )
    )


def reception_queue_row(row) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.flex(
                rx.vstack(
                    rx.text(row["patient_name"], font_weight="750", size="3"),
                    rx.text(
                        "Entrada: ",
                        row["entered_at"],
                        size="1",
                        color="var(--vitta-text-muted)",
                    ),
                    spacing="1",
                    align="start",
                ),
                priority_badge(row["priority"], row["priority_label"]),
                justify="between",
                align="start",
                width="100%",
                gap="0.75rem",
            ),
            rx.box(
                rx.text(
                    "Relato",
                    size="1",
                    font_weight="700",
                    color="var(--vitta-text-muted)",
                ),
                rx.text(
                    row["symptoms"],
                    size="2",
                    line_height="1.55",
                    overflow_wrap="anywhere",
                    margin_top="0.2rem",
                ),
                width="100%",
            ),
            rx.flex(
                rx.button(
                    "Reavaliar",
                    type="button",
                    variant="outline",
                    color_scheme="teal",
                    on_click=ReceptionQueueState.begin_reassess(
                        row["id"],
                        row["patient_name"],
                        row["symptoms"],
                        row["priority"],
                    ),
                    disabled=ReceptionQueueState.is_submitting,
                ),
                rx.button(
                    "Retirar da fila",
                    type="button",
                    variant="ghost",
                    color_scheme="red",
                    on_click=ReceptionQueueState.begin_withdraw(
                        row["id"], row["patient_name"]
                    ),
                    disabled=ReceptionQueueState.is_submitting,
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                gap="0.5rem",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        width="100%",
        padding="1rem",
        border="1px solid var(--vitta-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-surface)",
        role="listitem",
    )


def reassess_panel() -> rx.Component:
    return rx.cond(
        ReceptionQueueState.reassess_entry_id > 0,
        section_panel(
            rx.vstack(
                rx.box(
                    rx.heading("Reavaliar entrada", size="4"),
                    rx.text(
                        ReceptionQueueState.reassess_patient_name,
                        color="var(--vitta-text-muted)",
                        size="2",
                        margin_top="0.25rem",
                    ),
                    width="100%",
                ),
                rx.el.form(
                    rx.vstack(
                        rx.box(
                            field_label("Sintomas relatados", "reassess-symptoms"),
                            rx.el.textarea(
                                id="reassess-symptoms",
                                name="symptoms",
                                required=True,
                                max_length=4000,
                                rows=4,
                                class_name="vitta-textarea",
                                value=ReceptionQueueState.reassess_symptoms,
                                on_change=ReceptionQueueState.update_reassess_symptoms,
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.box(
                            field_label("Prioridade informada", "reassess-priority"),
                            priority_select(
                                name="priority",
                                control_id="reassess-priority",
                                value=ReceptionQueueState.reassess_priority,
                                on_change=ReceptionQueueState.update_reassess_priority,
                                disabled=ReceptionQueueState.is_submitting,
                            ),
                            width="100%",
                        ),
                        rx.flex(
                            rx.button(
                                "Cancelar",
                                type="button",
                                variant="ghost",
                                on_click=ReceptionQueueState.cancel_reassess,
                                disabled=ReceptionQueueState.is_submitting,
                            ),
                            rx.button(
                                "Salvar reavaliação",
                                type="submit",
                                color_scheme="teal",
                                high_contrast=True,
                                disabled=ReceptionQueueState.is_submitting,
                                loading=ReceptionQueueState.is_submitting,
                            ),
                            justify="end",
                            direction=rx.breakpoints(initial="column-reverse", sm="row"),
                            gap="0.5rem",
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    on_submit=ReceptionQueueState.reassess,
                    width="100%",
                ),
                spacing="4",
                width="100%",
                align="stretch",
            ),
            border_color="var(--vitta-primary)",
        ),
        rx.fragment(),
    )


def withdraw_panel() -> rx.Component:
    return rx.cond(
        ReceptionQueueState.withdraw_entry_id > 0,
        section_panel(
            rx.vstack(
                rx.heading("Confirmar retirada da fila", size="4"),
                rx.text(
                    "Paciente: ",
                    ReceptionQueueState.withdraw_patient_name,
                    size="2",
                    color="var(--vitta-text)",
                ),
                rx.text(
                    "A entrada sairá da fila ativa, mas o histórico será preservado.",
                    size="2",
                    color="var(--vitta-text-muted)",
                    line_height="1.5",
                ),
                rx.el.form(
                    rx.vstack(
                        rx.box(
                            field_label("Motivo da retirada", "withdraw-reason"),
                            rx.el.input(
                                id="withdraw-reason",
                                name="reason",
                                type="text",
                                required=True,
                                max_length=300,
                                class_name="vitta-input",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.flex(
                            rx.button(
                                "Cancelar",
                                type="button",
                                variant="ghost",
                                on_click=ReceptionQueueState.cancel_withdraw,
                                disabled=ReceptionQueueState.is_submitting,
                            ),
                            rx.button(
                                "Confirmar retirada",
                                type="submit",
                                color_scheme="red",
                                variant="outline",
                                disabled=ReceptionQueueState.is_submitting,
                                loading=ReceptionQueueState.is_submitting,
                            ),
                            justify="end",
                            direction=rx.breakpoints(initial="column-reverse", sm="row"),
                            gap="0.5rem",
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    on_submit=ReceptionQueueState.withdraw,
                    width="100%",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            border_color="var(--vitta-danger-border)",
        ),
        rx.fragment(),
    )


def active_queue_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.heading("Fila ativa", size="5"),
                    rx.text(
                        "Ordenação aplicada no servidor: Vermelho, Amarelo e Verde; em cada prioridade, entra primeiro quem chegou antes.",
                        color="var(--vitta-text-muted)",
                        size="2",
                        line_height="1.55",
                        margin_top="0.35rem",
                    ),
                    width="100%",
                ),
                rx.button(
                    "Atualizar fila",
                    type="button",
                    variant="outline",
                    color_scheme="teal",
                    on_click=ReceptionQueueState.load,
                    disabled=ReceptionQueueState.is_loading_queue
                    | ReceptionQueueState.is_submitting,
                    loading=ReceptionQueueState.is_loading_queue,
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                justify="between",
                align=rx.breakpoints(initial="stretch", sm="center"),
                gap="1rem",
                width="100%",
            ),
            rx.cond(
                ReceptionQueueState.is_loading_queue,
                rx.center(
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text(
                            "Carregando fila…",
                            size="2",
                            color="var(--vitta-text-muted)",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    min_height="8rem",
                    width="100%",
                    role="status",
                    aria_live="polite",
                ),
                rx.cond(
                    ReceptionQueueState.has_queue,
                    rx.vstack(
                        rx.foreach(
                            ReceptionQueueState.queue_rows,
                            reception_queue_row,
                        ),
                        spacing="3",
                        width="100%",
                        role="list",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.heading("Fila vazia", size="4"),
                            rx.text(
                                "Nenhum paciente está aguardando atendimento.",
                                color="var(--vitta-text-muted)",
                                size="2",
                                text_align="center",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        min_height="8rem",
                        width="100%",
                    ),
                ),
            ),
            spacing="5",
            width="100%",
            align="stretch",
        )
    )


def doctor_waiting_summary() -> rx.Component:
    return section_panel(
        rx.flex(
            rx.box(
                rx.heading("Fila de atendimento", size="5"),
                rx.text(
                    "A chamada respeita a prioridade informada e a ordem de entrada. A seleção é confirmada no servidor.",
                    color="var(--vitta-text-muted)",
                    size="2",
                    line_height="1.55",
                    margin_top="0.35rem",
                    max_width="58ch",
                ),
            ),
            rx.box(
                rx.text(
                    DoctorQueueState.waiting_count,
                    font_size="2rem",
                    font_weight="800",
                    line_height="1",
                    color="var(--vitta-primary)",
                ),
                rx.text(
                    "aguardando",
                    size="1",
                    color="var(--vitta-text-muted)",
                    margin_top="0.25rem",
                ),
                text_align=rx.breakpoints(initial="left", sm="right"),
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", sm="center"),
            gap="1rem",
            width="100%",
        )
    )


def doctor_active_panel() -> rx.Component:
    return rx.cond(
        DoctorQueueState.has_active,
        section_panel(
            rx.vstack(
                rx.flex(
                    rx.box(
                        rx.heading("Atendimento ativo", size="5"),
                        rx.text(
                            DoctorQueueState.active_patient_name,
                            font_weight="750",
                            size="4",
                            margin_top="0.4rem",
                        ),
                        rx.text(
                            "Chamado às ",
                            DoctorQueueState.active_called_at,
                            size="1",
                            color="var(--vitta-text-muted)",
                            margin_top="0.2rem",
                        ),
                    ),
                    priority_badge(
                        DoctorQueueState.active_priority,
                        DoctorQueueState.active_priority_label,
                    ),
                    justify="between",
                    align="start",
                    width="100%",
                    gap="0.75rem",
                ),
                rx.box(
                    rx.text(
                        "Relato recebido na recepção",
                        size="1",
                        font_weight="700",
                        color="var(--vitta-text-muted)",
                    ),
                    rx.text(
                        DoctorQueueState.active_symptoms,
                        line_height="1.65",
                        overflow_wrap="anywhere",
                        margin_top="0.35rem",
                    ),
                    width="100%",
                    padding="1rem",
                    background="var(--vitta-surface-muted)",
                    border_radius="var(--vitta-radius-control)",
                ),
                rx.button(
                    "Finalizar atendimento",
                    type="button",
                    color_scheme="teal",
                    high_contrast=True,
                    min_height="3rem",
                    width=rx.breakpoints(initial="100%", sm="auto"),
                    on_click=DoctorQueueState.finish_active,
                    disabled=DoctorQueueState.is_submitting,
                    loading=DoctorQueueState.is_submitting,
                ),
                spacing="4",
                align="start",
                width="100%",
            ),
            border_color="var(--vitta-primary)",
        ),
        section_panel(
            rx.center(
                rx.vstack(
                    rx.heading("Nenhum atendimento ativo", size="4"),
                    rx.text(
                        "Quando estiver disponível, chame o próximo paciente da fila.",
                        color="var(--vitta-text-muted)",
                        size="2",
                        text_align="center",
                    ),
                    rx.button(
                        "Chamar próximo",
                        type="button",
                        color_scheme="teal",
                        high_contrast=True,
                        min_height="3rem",
                        on_click=DoctorQueueState.claim_next,
                        disabled=DoctorQueueState.is_submitting
                        | (DoctorQueueState.waiting_count == 0),
                        loading=DoctorQueueState.is_submitting,
                    ),
                    spacing="4",
                    align="center",
                ),
                min_height="13rem",
                width="100%",
            )
        ),
    )
