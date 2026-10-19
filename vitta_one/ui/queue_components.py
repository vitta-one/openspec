"""Reusable UI for the patient reception queue capability."""

import reflex as rx

from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState
from vitta_one.ui.components import empty_state, feedback_region, field_label, section_panel


def priority_select(
    *,
    name: str,
    control_id: str,
    value=None,
    on_change=None,
    default_value: str | None = None,
    described_by: str | None = None,
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
            aria_describedby=described_by,
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


def selected_patient_operations() -> rx.Component:
    return rx.cond(
        ReceptionQueueState.selected_patient_id > 0,
        rx.vstack(
            section_panel(
                rx.vstack(
                    rx.heading("Cadastro operacional", size="4"),
                    rx.text(
                        "Atualize somente nome e telefone. O CPF e o vínculo do portal não podem ser alterados aqui.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        line_height="1.5",
                    ),
                    rx.el.form(
                        rx.flex(
                            rx.box(
                                field_label("Nome completo", "patient-edit-name"),
                                rx.el.input(
                                    id="patient-edit-name",
                                    name="name",
                                    value=ReceptionQueueState.selected_patient_name,
                                    on_change=ReceptionQueueState.update_selected_patient_name,
                                    required=True,
                                    max_length=160,
                                    class_name="vitta-input",
                                    margin_top="0.4rem",
                                ),
                                width="100%",
                            ),
                            rx.box(
                                field_label("Telefone", "patient-edit-phone"),
                                rx.el.input(
                                    id="patient-edit-phone",
                                    name="phone",
                                    type="tel",
                                    value=ReceptionQueueState.selected_patient_phone,
                                    on_change=ReceptionQueueState.update_selected_patient_phone,
                                    max_length=20,
                                    class_name="vitta-input",
                                    margin_top="0.4rem",
                                ),
                                width="100%",
                            ),
                            direction=rx.breakpoints(initial="column", md="row"),
                            gap="3",
                            width="100%",
                        ),
                        rx.button(
                            "Salvar cadastro",
                            type="submit",
                            variant="outline",
                            color_scheme="teal",
                            disabled=ReceptionQueueState.is_submitting,
                            loading=ReceptionQueueState.is_submitting,
                        ),
                        no_validate=True,
                        on_submit=ReceptionQueueState.update_selected_patient,
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                    align="stretch",
                )
            ),
            section_panel(
                rx.vstack(
                    rx.heading("Acesso ao portal", size="4"),
                    rx.text(
                        ReceptionQueueState.selected_patient_portal_status,
                        role="status",
                        aria_live="polite",
                        color="var(--vitta-primary)",
                        font_weight="700",
                    ),
                    rx.text(
                        "O cadastro não cria uma conta. Envie um convite somente após confirmar consentimento com o paciente.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        line_height="1.5",
                    ),
                    rx.el.form(
                        rx.box(
                            field_label("E-mail para login", "patient-portal-email"),
                            rx.el.input(
                                id="patient-portal-email",
                                name="email",
                                type="email",
                                auto_complete="email",
                                required=True,
                                max_length=320,
                                class_name="vitta-input",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.flex(
                            rx.el.input(
                                id="patient-portal-consent",
                                name="consent_confirmed",
                                type="checkbox",
                                value="true",
                                required=True,
                                aria_label="Consentimento confirmado",
                            ),
                            rx.text(
                                "Confirmo que o paciente consentiu em receber o convite de ativação.",
                                size="2",
                                line_height="1.5",
                            ),
                            gap="2",
                            align="start",
                        ),
                        rx.button(
                            "Enviar convite de ativação",
                            type="submit",
                            min_height="2.75rem",
                            color_scheme="teal",
                            high_contrast=True,
                            disabled=ReceptionQueueState.is_submitting
                            | (ReceptionQueueState.selected_patient_portal_status == "Acesso ao portal ativo"),
                            loading=ReceptionQueueState.is_submitting,
                        ),
                        no_validate=True,
                        on_submit=ReceptionQueueState.issue_patient_portal_invitation,
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                    align="stretch",
                )
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        rx.fragment(),
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
                                min_length=11,
                                max_length=14,
                                class_name="vitta-input",
                                placeholder="000.000.000-00",
                                aria_describedby=rx.cond(
                                    ReceptionQueueState.error_message != "",
                                    "queue-feedback",
                                    "",
                                ),
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
                    no_validate=True,
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
                                min_length=11,
                                max_length=14,
                                class_name="vitta-input",
                                placeholder="000.000.000-00",
                                aria_describedby=rx.cond(
                                    ReceptionQueueState.error_message != "",
                                    "queue-feedback",
                                    "",
                                ),
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.box(
                            field_label("Telefone (opcional)", "patient-create-phone"),
                            rx.el.input(
                                id="patient-create-phone",
                                name="phone",
                                type="tel",
                                input_mode="tel",
                                auto_complete="tel-national",
                                max_length=20,
                                class_name="vitta-input",
                                placeholder="(11) 98765-4321",
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
                    no_validate=True,
                    on_submit=ReceptionQueueState.create_patient,
                    width="100%",
                ),
                direction=rx.breakpoints(initial="column", lg="row"),
                gap="1.25rem",
                align="start",
                width="100%",
            ),
            patient_selection_summary(),
            selected_patient_operations(),
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
                                described_by="queue-priority-help",
                                disabled=ReceptionQueueState.is_submitting,
                            ),
                            rx.text(
                                "Escolha exatamente a classificação recebida: Vermelho, Amarelo ou Verde.",
                                id="queue-priority-help",
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
                    no_validate=True,
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
                    rx.hstack(
                        rx.text(row["patient_name"], font_weight="750", size="3"),
                        rx.cond(
                            row["is_scheduled"],
                            rx.badge(
                                "Consulta agendada",
                                color_scheme="teal",
                                variant="soft",
                                high_contrast=True,
                            ),
                            rx.badge(
                                "Atendimento avulso",
                                color_scheme="gray",
                                variant="soft",
                            ),
                        ),
                        spacing="2",
                        align="center",
                        flex_wrap="wrap",
                    ),
                    rx.text(
                        "Entrada: ",
                        row["entered_at"],
                        size="1",
                        color="var(--vitta-text-muted)",
                    ),
                    rx.cond(
                        row["is_scheduled"],
                        rx.text(
                            row["professional_name"],
                            " · ",
                            row["scheduled_at"],
                            size="1",
                            color="var(--vitta-text-subtle)",
                            class_name="vitta-tabular",
                        ),
                        rx.fragment(),
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
                        row["id"],
                        row["patient_name"],
                        row["is_scheduled"],
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
                                described_by="reassess-priority-help",
                                disabled=ReceptionQueueState.is_submitting,
                            ),
                            rx.text(
                                "A prioridade só muda por esta reavaliação manual.",
                                id="reassess-priority-help",
                                size="1",
                                color="var(--vitta-text-muted)",
                                margin_top="0.4rem",
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
                    no_validate=True,
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
                rx.cond(
                    ReceptionQueueState.withdraw_is_scheduled,
                    rx.text(
                        "A entrada sairá da fila e a Consulta confirmada será cancelada. O histórico dos dois registros será preservado.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        line_height="1.5",
                    ),
                    rx.text(
                        "A entrada sairá da fila ativa, mas o histórico será preservado.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        line_height="1.5",
                    ),
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
                    no_validate=True,
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
                    "A chamada respeita prioridade e ordem de chegada. Consultas agendadas são encaminhadas ao médico marcado; atendimentos de pronto-socorro seguem a fila compartilhada.",
                    color="var(--vitta-text-muted)",
                    size="2",
                    line_height="1.55",
                    margin_top="0.35rem",
                    max_width="58ch",
                ),
            ),
            rx.vstack(
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
                rx.button(
                    "Atualizar fila",
                    type="button",
                    size="2",
                    variant="ghost",
                    color_scheme="teal",
                    on_click=DoctorQueueState.load,
                    disabled=DoctorQueueState.is_loading
                    | DoctorQueueState.is_submitting,
                    loading=DoctorQueueState.is_loading,
                ),
                spacing="2",
                align=rx.breakpoints(initial="start", sm="end"),
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", sm="center"),
            gap="1rem",
            width="100%",
        )
    )


def _clinical_field(
    *,
    label: str,
    control_id: str,
    value,
    on_change,
    max_length: int,
    rows: int,
    help_text: str,
) -> rx.Component:
    return rx.box(
        field_label(label, control_id),
        rx.el.textarea(
            id=control_id,
            name=control_id,
            value=value,
            on_change=on_change,
            max_length=max_length,
            rows=rows,
            class_name="vitta-textarea vitta-clinical-textarea",
            aria_describedby=f"{control_id}-help",
            disabled=DoctorQueueState.is_saving_clinical | DoctorQueueState.is_submitting,
            margin_top="0.4rem",
        ),
        rx.text(
            help_text,
            id=f"{control_id}-help",
            size="1",
            color="var(--vitta-text-subtle)",
            margin_top="0.35rem",
        ),
        width="100%",
    )


def _history_value(label: str, value) -> rx.Component:
    return rx.box(
        rx.text(
            label,
            size="1",
            font_weight="750",
            color="var(--vitta-text-muted)",
        ),
        rx.cond(
            value != "",
            rx.text(
                value,
                size="2",
                line_height="1.6",
                white_space="pre-wrap",
                overflow_wrap="anywhere",
                margin_top="0.25rem",
            ),
            rx.text(
                "Não registrado",
                size="2",
                color="var(--vitta-text-subtle)",
                margin_top="0.25rem",
            ),
        ),
        width="100%",
    )


def _prescription_item_readonly(item) -> rx.Component:
    return rx.box(
        rx.text(
            item["medication_or_item"],
            font_weight="800",
            size="2",
            overflow_wrap="anywhere",
        ),
        rx.text(
            item["instructions"],
            size="2",
            line_height="1.6",
            white_space="pre-wrap",
            overflow_wrap="anywhere",
            margin_top="0.3rem",
        ),
        rx.cond(
            item["notes"] != "",
            rx.text(
                item["notes"],
                size="1",
                color="var(--vitta-text-muted)",
                line_height="1.5",
                white_space="pre-wrap",
                overflow_wrap="anywhere",
                margin_top="0.35rem",
            ),
            rx.fragment(),
        ),
        class_name="vitta-prescription-item",
        role="listitem",
    )


def _history_prescription_card(row) -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            rx.flex(
                rx.box(
                    rx.text("Prescrição", font_weight="800", size="2"),
                    rx.text(
                        row["created_at"],
                        size="1",
                        color="var(--vitta-text-subtle)",
                        class_name="vitta-tabular",
                        margin_top="0.1rem",
                    ),
                ),
                rx.badge(
                    row["item_count"],
                    " itens",
                    color_scheme="teal",
                    variant="soft",
                ),
                justify="between",
                align="center",
                gap="0.75rem",
                width="100%",
            ),
            class_name="vitta-disclosure-summary",
        ),
        rx.vstack(
            rx.vstack(
                rx.foreach(row["items"], _prescription_item_readonly),
                spacing="2",
                align="stretch",
                width="100%",
                role="list",
            ),
            rx.cond(
                row["general_notes"] != "",
                rx.box(
                    rx.text(
                        "Observações gerais",
                        size="1",
                        font_weight="750",
                        color="var(--vitta-text-muted)",
                    ),
                    rx.text(
                        row["general_notes"],
                        size="2",
                        line_height="1.55",
                        white_space="pre-wrap",
                        overflow_wrap="anywhere",
                        margin_top="0.25rem",
                    ),
                    width="100%",
                ),
                rx.fragment(),
            ),
            spacing="3",
            align="stretch",
            width="100%",
            padding_top="0.75rem",
        ),
        class_name="vitta-prescription-history-disclosure",
    )


def _history_prescriptions(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.text("Prescrições", font_weight="750", size="2"),
            rx.cond(
                row["prescription_count"] > 0,
                rx.badge(
                    row["prescription_count"],
                    color_scheme="teal",
                    variant="soft",
                ),
                rx.fragment(),
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.cond(
            row["prescription_count"] > 0,
            rx.vstack(
                rx.foreach(row["prescriptions"], _history_prescription_card),
                spacing="2",
                align="stretch",
                width="100%",
                margin_top="0.65rem",
            ),
            rx.text(
                "Sem prescrições neste atendimento.",
                size="2",
                color="var(--vitta-text-subtle)",
                margin_top="0.5rem",
            ),
        ),
        width="100%",
        padding_top="0.85rem",
        border_top="1px solid var(--vitta-border)",
    )


def _clinical_history_card(row) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.text(row["completed_at"], font_weight="800", size="2"),
                    rx.text(
                        row["professional_name"],
                        size="1",
                        color="var(--vitta-text-muted)",
                        margin_top="0.15rem",
                    ),
                ),
                rx.hstack(
                    rx.cond(
                        row["prescription_count"] > 0,
                        rx.badge(
                            row["prescription_count"],
                            " prescrição(ões)",
                            color_scheme="teal",
                            variant="soft",
                        ),
                        rx.fragment(),
                    ),
                    rx.badge(
                        "Concluído",
                        color_scheme="green",
                        variant="soft",
                        high_contrast=True,
                    ),
                    spacing="2",
                    flex_wrap="wrap",
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                justify="between",
                align=rx.breakpoints(initial="stretch", sm="start"),
                gap="0.75rem",
                width="100%",
            ),
            rx.grid(
                _history_value("Queixa principal", row["chief_complaint"]),
                _history_value("Anamnese", row["anamnesis"]),
                _history_value("Diagnóstico", row["diagnosis"]),
                _history_value("Conduta e observações", row["conduct_notes"]),
                columns=rx.breakpoints(initial="1", lg="2"),
                gap="0.9rem",
                width="100%",
            ),
            _history_prescriptions(row),
            spacing="3",
            align="stretch",
            width="100%",
        ),
        class_name="vitta-clinical-history-card",
        role="listitem",
    )


def clinical_history_panel() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.heading("Histórico clínico", size="4"),
                rx.text(
                    "Atendimentos concluídos e suas prescrições persistidas.",
                    size="2",
                    color="var(--vitta-text-muted)",
                    margin_top="0.25rem",
                ),
            ),
            rx.cond(
                DoctorQueueState.clinical_history_total_count > 0,
                rx.badge(
                    DoctorQueueState.clinical_history_total_count,
                    " registros",
                    color_scheme="gray",
                    variant="soft",
                ),
                rx.fragment(),
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", sm="start"),
            gap="0.5rem",
            width="100%",
        ),
        rx.cond(
            DoctorQueueState.clinical_history.length() > 0,
            rx.vstack(
                rx.vstack(
                    rx.foreach(
                        DoctorQueueState.clinical_history,
                        _clinical_history_card,
                    ),
                    spacing="3",
                    align="stretch",
                    width="100%",
                    role="list",
                ),
                rx.flex(
                    rx.text(
                        "Página ",
                        DoctorQueueState.clinical_history_page,
                        " de ",
                        DoctorQueueState.clinical_history_total_pages,
                        size="1",
                        color="var(--vitta-text-muted)",
                    ),
                    rx.hstack(
                        rx.button(
                            "Anterior",
                            type="button",
                            variant="outline",
                            color_scheme="teal",
                            size="2",
                            on_click=DoctorQueueState.previous_clinical_history_page,
                            disabled=~DoctorQueueState.can_previous_clinical_history_page
                            | DoctorQueueState.is_loading,
                        ),
                        rx.button(
                            "Próxima",
                            type="button",
                            variant="outline",
                            color_scheme="teal",
                            size="2",
                            on_click=DoctorQueueState.next_clinical_history_page,
                            disabled=~DoctorQueueState.can_next_clinical_history_page
                            | DoctorQueueState.is_loading,
                        ),
                        spacing="2",
                    ),
                    direction=rx.breakpoints(initial="column", sm="row"),
                    justify="between",
                    align=rx.breakpoints(initial="stretch", sm="center"),
                    gap="0.6rem",
                    width="100%",
                ),
                spacing="3",
                align="stretch",
                width="100%",
                margin_top="1rem",
            ),
            empty_state(
                "history",
                "Sem atendimentos clínicos anteriores",
                "Quando este paciente possuir Consultas concluídas, o histórico clínico aparecerá aqui.",
            ),
        ),
        width="100%",
        margin_top="1.25rem",
    )


def _prescription_item_editor_row(item, prescription) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(
                    item["medication_or_item"],
                    font_weight="800",
                    size="2",
                    overflow_wrap="anywhere",
                ),
                rx.text(
                    item["instructions"],
                    size="2",
                    line_height="1.55",
                    white_space="pre-wrap",
                    overflow_wrap="anywhere",
                    margin_top="0.3rem",
                ),
                rx.cond(
                    item["notes"] != "",
                    rx.text(
                        item["notes"],
                        size="1",
                        color="var(--vitta-text-muted)",
                        line_height="1.5",
                        white_space="pre-wrap",
                        overflow_wrap="anywhere",
                        margin_top="0.35rem",
                    ),
                    rx.fragment(),
                ),
                width="100%",
            ),
            rx.hstack(
                rx.button(
                    "Editar",
                    type="button",
                    variant="ghost",
                    color_scheme="teal",
                    size="1",
                    on_click=DoctorQueueState.begin_edit_prescription_item(
                        prescription["id"],
                        item["id"],
                        item["medication_or_item"],
                        item["instructions"],
                        item["notes"],
                    ),
                    disabled=DoctorQueueState.is_prescription_submitting,
                ),
                rx.button(
                    "Remover",
                    type="button",
                    variant="ghost",
                    color_scheme="red",
                    size="1",
                    on_click=DoctorQueueState.begin_remove_prescription_item(
                        prescription["id"],
                        item["id"],
                        item["medication_or_item"],
                    ),
                    disabled=(prescription["item_count"] <= 1)
                    | DoctorQueueState.is_prescription_submitting,
                    title="Remover item. A Prescrição deve manter pelo menos um item persistido.",
                ),
                spacing="1",
                flex_wrap="wrap",
            ),
            direction=rx.breakpoints(initial="column", md="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", md="start"),
            gap="0.75rem",
            width="100%",
        ),
        class_name="vitta-prescription-item",
        role="listitem",
    )


def _current_prescription_card(row) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.text("Prescrição", size="3", font_weight="850"),
                    rx.text(
                        row["created_at"],
                        size="1",
                        color="var(--vitta-text-subtle)",
                        class_name="vitta-tabular",
                        margin_top="0.15rem",
                    ),
                ),
                rx.hstack(
                    rx.badge(
                        row["item_count"],
                        " itens",
                        color_scheme="teal",
                        variant="soft",
                    ),
                    rx.button(
                        "Visualizar para impressão",
                        type="button",
                        variant="outline",
                        color_scheme="teal",
                        size="1",
                        on_click=DoctorQueueState.open_prescription_print(row["id"]),
                        disabled=DoctorQueueState.is_prescription_submitting,
                    ),
                    spacing="2",
                    flex_wrap="wrap",
                ),
                direction=rx.breakpoints(initial="column", md="row"),
                justify="between",
                align=rx.breakpoints(initial="stretch", md="center"),
                gap="0.75rem",
                width="100%",
            ),
            rx.vstack(
                rx.foreach(
                    row["items"],
                    lambda item: _prescription_item_editor_row(item, row),
                ),
                spacing="2",
                align="stretch",
                width="100%",
                role="list",
            ),
            rx.cond(
                row["general_notes"] != "",
                rx.box(
                    rx.text(
                        "Observações gerais",
                        size="1",
                        font_weight="750",
                        color="var(--vitta-text-muted)",
                    ),
                    rx.text(
                        row["general_notes"],
                        size="2",
                        line_height="1.55",
                        white_space="pre-wrap",
                        overflow_wrap="anywhere",
                        margin_top="0.25rem",
                    ),
                    width="100%",
                    padding="0.8rem",
                    background="var(--vitta-surface-muted)",
                    border_radius="var(--vitta-radius-control)",
                ),
                rx.fragment(),
            ),
            rx.flex(
                rx.hstack(
                    rx.button(
                        "Adicionar item",
                        type="button",
                        variant="outline",
                        color_scheme="teal",
                        size="2",
                        on_click=DoctorQueueState.begin_add_prescription_item(row["id"]),
                        disabled=DoctorQueueState.is_prescription_submitting,
                    ),
                    rx.button(
                        "Editar observações gerais",
                        type="button",
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                        on_click=DoctorQueueState.begin_prescription_notes(
                            row["id"],
                            row["general_notes"],
                        ),
                        disabled=DoctorQueueState.is_prescription_submitting,
                    ),
                    spacing="2",
                    flex_wrap="wrap",
                ),
                rx.button(
                    "Excluir prescrição",
                    type="button",
                    variant="ghost",
                    color_scheme="red",
                    size="2",
                    on_click=DoctorQueueState.begin_delete_prescription(row["id"]),
                    disabled=DoctorQueueState.is_prescription_submitting,
                ),
                direction=rx.breakpoints(initial="column", md="row"),
                justify="between",
                align=rx.breakpoints(initial="stretch", md="center"),
                gap="0.6rem",
                width="100%",
            ),
            spacing="3",
            align="stretch",
            width="100%",
        ),
        class_name="vitta-prescription-card",
        role="listitem",
    )


def prescription_panel() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.heading("Prescrições", size="4"),
                rx.text(
                    "Crie documentos simples com itens e orientações. Assinatura digital entra em uma etapa posterior.",
                    size="2",
                    color="var(--vitta-text-muted)",
                    line_height="1.55",
                    margin_top="0.25rem",
                ),
            ),
            rx.button(
                "Nova prescrição",
                id="vitta-new-prescription-trigger",
                type="button",
                color_scheme="teal",
                high_contrast=True,
                on_click=DoctorQueueState.begin_new_prescription,
                disabled=DoctorQueueState.is_prescription_submitting
                | DoctorQueueState.is_submitting,
                loading=DoctorQueueState.is_prescription_submitting,
                width=rx.breakpoints(initial="100%", sm="auto"),
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", sm="start"),
            gap="0.75rem",
            width="100%",
        ),
        rx.cond(
            DoctorQueueState.prescriptions.length() > 0,
            rx.vstack(
                rx.foreach(DoctorQueueState.prescriptions, _current_prescription_card),
                spacing="3",
                align="stretch",
                width="100%",
                role="list",
                margin_top="1rem",
            ),
            empty_state(
                "clipboard_list",
                "Nenhuma prescrição neste atendimento",
                "Crie uma Prescrição quando houver orientação medicamentosa ou outro item a registrar.",
            ),
        ),
        _new_prescription_dialog(),
        _prescription_item_dialog(),
        _prescription_notes_dialog(),
        _delete_prescription_dialog(),
        _remove_prescription_item_dialog(),
        class_name="vitta-prescription-workspace",
        width="100%",
        margin_top="1.25rem",
    )


def _prescription_text_field(
    *,
    label: str,
    control_id: str,
    value,
    on_change,
    max_length: int,
    rows: int,
    help_text: str,
    auto_focus: bool = False,
) -> rx.Component:
    return rx.box(
        field_label(label, control_id),
        rx.el.textarea(
            id=control_id,
            name=control_id,
            value=value,
            on_change=on_change,
            max_length=max_length,
            rows=rows,
            class_name="vitta-textarea vitta-clinical-textarea",
            aria_describedby=f"{control_id}-help",
            disabled=DoctorQueueState.is_prescription_submitting,
            margin_top="0.4rem",
            auto_focus=auto_focus,
        ),
        rx.text(
            help_text,
            id=f"{control_id}-help",
            size="1",
            color="var(--vitta-text-subtle)",
            margin_top="0.35rem",
        ),
        width="100%",
    )


def _new_prescription_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nova prescrição"),
            rx.dialog.description(
                "A Prescrição será criada junto do primeiro item. Nenhum documento vazio é salvo.",
                margin_top="0.35rem",
                margin_bottom="1rem",
            ),
            rx.el.form(
                rx.vstack(
                    _prescription_text_field(
                        label="Medicamento ou item",
                        control_id="new-prescription-medication",
                        value=DoctorQueueState.new_prescription_medication,
                        on_change=DoctorQueueState.update_new_prescription_medication,
                        max_length=300,
                        rows=2,
                        help_text="Obrigatório · até 300 caracteres.",
                        auto_focus=True,
                    ),
                    _prescription_text_field(
                        label="Orientação / posologia",
                        control_id="new-prescription-instructions",
                        value=DoctorQueueState.new_prescription_instructions,
                        on_change=DoctorQueueState.update_new_prescription_instructions,
                        max_length=2000,
                        rows=4,
                        help_text="Obrigatório · até 2.000 caracteres.",
                    ),
                    _prescription_text_field(
                        label="Observações do item",
                        control_id="new-prescription-item-notes",
                        value=DoctorQueueState.new_prescription_item_notes,
                        on_change=DoctorQueueState.update_new_prescription_item_notes,
                        max_length=2000,
                        rows=3,
                        help_text="Opcional · até 2.000 caracteres.",
                    ),
                    _prescription_text_field(
                        label="Observações gerais da prescrição",
                        control_id="new-prescription-general-notes",
                        value=DoctorQueueState.new_prescription_general_notes,
                        on_change=DoctorQueueState.update_new_prescription_general_notes,
                        max_length=4000,
                        rows=3,
                        help_text="Opcional · até 4.000 caracteres.",
                    ),
                    rx.flex(
                        rx.dialog.close(
                            rx.button(
                                "Cancelar",
                                type="button",
                                variant="ghost",
                                disabled=DoctorQueueState.is_prescription_submitting,
                            )
                        ),
                        rx.button(
                            "Criar prescrição",
                            type="submit",
                            color_scheme="teal",
                            high_contrast=True,
                            disabled=DoctorQueueState.is_prescription_submitting,
                            loading=DoctorQueueState.is_prescription_submitting,
                        ),
                        direction=rx.breakpoints(initial="column-reverse", sm="row"),
                        justify="end",
                        gap="0.5rem",
                        width="100%",
                    ),
                    spacing="4",
                    align="stretch",
                    width="100%",
                ),
                on_submit=DoctorQueueState.create_prescription,
                no_validate=True,
                width="100%",
            ),
            on_close_auto_focus=rx.call_script(
                "document.getElementById('vitta-new-prescription-trigger')?.focus()"
            ),
            class_name="vitta-dialog-content",
            max_width="42rem",
            max_height="min(90dvh, 48rem)",
            overflow_y="auto",
        ),
        open=DoctorQueueState.new_prescription_dialog_open,
        on_open_change=DoctorQueueState.set_new_prescription_dialog_open,
    )


def _prescription_item_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    DoctorQueueState.prescription_item_mode == "edit",
                    "Editar item",
                    "Adicionar item",
                )
            ),
            rx.dialog.description(
                "Registre o item e a orientação exatamente como devem permanecer na Prescrição.",
                margin_top="0.35rem",
                margin_bottom="1rem",
            ),
            rx.el.form(
                rx.vstack(
                    _prescription_text_field(
                        label="Medicamento ou item",
                        control_id="prescription-item-medication",
                        value=DoctorQueueState.prescription_item_medication,
                        on_change=DoctorQueueState.update_prescription_item_medication,
                        max_length=300,
                        rows=2,
                        help_text="Obrigatório · até 300 caracteres.",
                        auto_focus=True,
                    ),
                    _prescription_text_field(
                        label="Orientação / posologia",
                        control_id="prescription-item-instructions",
                        value=DoctorQueueState.prescription_item_instructions,
                        on_change=DoctorQueueState.update_prescription_item_instructions,
                        max_length=2000,
                        rows=4,
                        help_text="Obrigatório · até 2.000 caracteres.",
                    ),
                    _prescription_text_field(
                        label="Observações",
                        control_id="prescription-item-notes",
                        value=DoctorQueueState.prescription_item_notes,
                        on_change=DoctorQueueState.update_prescription_item_notes,
                        max_length=2000,
                        rows=3,
                        help_text="Opcional · até 2.000 caracteres.",
                    ),
                    rx.flex(
                        rx.dialog.close(
                            rx.button(
                                "Cancelar",
                                type="button",
                                variant="ghost",
                                disabled=DoctorQueueState.is_prescription_submitting,
                            )
                        ),
                        rx.button(
                            rx.cond(
                                DoctorQueueState.prescription_item_mode == "edit",
                                "Salvar item",
                                "Adicionar item",
                            ),
                            type="submit",
                            color_scheme="teal",
                            high_contrast=True,
                            disabled=DoctorQueueState.is_prescription_submitting,
                            loading=DoctorQueueState.is_prescription_submitting,
                        ),
                        direction=rx.breakpoints(initial="column-reverse", sm="row"),
                        justify="end",
                        gap="0.5rem",
                        width="100%",
                    ),
                    spacing="4",
                    align="stretch",
                    width="100%",
                ),
                on_submit=DoctorQueueState.submit_prescription_item,
                no_validate=True,
                width="100%",
            ),
            class_name="vitta-dialog-content",
            max_width="40rem",
            max_height="min(90dvh, 44rem)",
            overflow_y="auto",
        ),
        open=DoctorQueueState.prescription_item_dialog_open,
        on_open_change=DoctorQueueState.set_prescription_item_dialog_open,
    )


def _prescription_notes_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Observações gerais"),
            rx.dialog.description(
                "Use este campo para orientações que pertencem ao documento inteiro, não a um item específico.",
                margin_top="0.35rem",
                margin_bottom="1rem",
            ),
            rx.el.form(
                rx.vstack(
                    _prescription_text_field(
                        label="Observações gerais",
                        control_id="prescription-general-notes",
                        value=DoctorQueueState.prescription_general_notes,
                        on_change=DoctorQueueState.update_prescription_general_notes,
                        max_length=4000,
                        rows=5,
                        help_text="Opcional · até 4.000 caracteres.",
                        auto_focus=True,
                    ),
                    rx.flex(
                        rx.dialog.close(
                            rx.button(
                                "Cancelar",
                                type="button",
                                variant="ghost",
                                disabled=DoctorQueueState.is_prescription_submitting,
                            )
                        ),
                        rx.button(
                            "Salvar observações",
                            type="submit",
                            color_scheme="teal",
                            high_contrast=True,
                            disabled=DoctorQueueState.is_prescription_submitting,
                            loading=DoctorQueueState.is_prescription_submitting,
                        ),
                        direction=rx.breakpoints(initial="column-reverse", sm="row"),
                        justify="end",
                        gap="0.5rem",
                        width="100%",
                    ),
                    spacing="4",
                    align="stretch",
                    width="100%",
                ),
                on_submit=DoctorQueueState.save_prescription_notes,
                no_validate=True,
                width="100%",
            ),
            class_name="vitta-dialog-content",
            max_width="38rem",
        ),
        open=DoctorQueueState.prescription_notes_dialog_open,
        on_open_change=DoctorQueueState.set_prescription_notes_dialog_open,
    )


def _delete_prescription_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Excluir prescrição?"),
            rx.dialog.description(
                "A Prescrição e todos os itens serão removidos deste atendimento em andamento. Após a Consulta ser concluída, essa exclusão não será permitida.",
                margin_top="0.35rem",
                margin_bottom="1rem",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Manter prescrição",
                        type="button",
                        variant="ghost",
                        disabled=DoctorQueueState.is_prescription_submitting,
                        auto_focus=True,
                    )
                ),
                rx.button(
                    "Excluir prescrição",
                    type="button",
                    color_scheme="red",
                    high_contrast=True,
                    on_click=DoctorQueueState.confirm_delete_prescription,
                    disabled=DoctorQueueState.is_prescription_submitting,
                    loading=DoctorQueueState.is_prescription_submitting,
                ),
                direction=rx.breakpoints(initial="column-reverse", sm="row"),
                justify="end",
                gap="0.5rem",
                width="100%",
            ),
            class_name="vitta-dialog-content",
            max_width="34rem",
        ),
        open=DoctorQueueState.delete_prescription_dialog_open,
        on_open_change=DoctorQueueState.set_delete_prescription_dialog_open,
    )


def _remove_prescription_item_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Remover item?"),
            rx.dialog.description(
                "O item será removido desta Prescrição em andamento.",
                margin_top="0.35rem",
            ),
            rx.text(
                DoctorQueueState.remove_prescription_item_name,
                font_weight="800",
                size="2",
                margin_top="0.8rem",
                overflow_wrap="anywhere",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Manter item",
                        type="button",
                        variant="ghost",
                        disabled=DoctorQueueState.is_prescription_submitting,
                        auto_focus=True,
                    )
                ),
                rx.button(
                    "Remover item",
                    type="button",
                    color_scheme="red",
                    high_contrast=True,
                    on_click=DoctorQueueState.confirm_remove_prescription_item,
                    disabled=DoctorQueueState.is_prescription_submitting,
                    loading=DoctorQueueState.is_prescription_submitting,
                ),
                direction=rx.breakpoints(initial="column-reverse", sm="row"),
                justify="end",
                gap="0.5rem",
                width="100%",
                margin_top="1.25rem",
            ),
            class_name="vitta-dialog-content",
            max_width="34rem",
        ),
        open=DoctorQueueState.remove_prescription_item_dialog_open,
        on_open_change=DoctorQueueState.set_remove_prescription_item_dialog_open,
    )


def clinical_care_form() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.heading("Atendimento clínico", size="4"),
                rx.text(
                    "Registre o essencial do atendimento atual.",
                    size="2",
                    color="var(--vitta-text-muted)",
                    line_height="1.55",
                    margin_top="0.25rem",
                ),
            ),
            rx.cond(
                DoctorQueueState.clinical_is_dirty,
                rx.badge(
                    "Alterações não salvas",
                    color_scheme="amber",
                    variant="soft",
                    high_contrast=True,
                ),
                rx.badge(
                    "Salvo",
                    color_scheme="green",
                    variant="soft",
                    high_contrast=True,
                ),
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", sm="start"),
            gap="0.65rem",
            width="100%",
        ),
        rx.el.form(
            rx.vstack(
                _clinical_field(
                    label="Queixa principal",
                    control_id="clinical-chief-complaint",
                    value=DoctorQueueState.clinical_chief_complaint,
                    on_change=DoctorQueueState.update_clinical_chief_complaint,
                    max_length=4000,
                    rows=3,
                    help_text="Até 4.000 caracteres.",
                ),
                _clinical_field(
                    label="Anamnese",
                    control_id="clinical-anamnesis",
                    value=DoctorQueueState.clinical_anamnesis,
                    on_change=DoctorQueueState.update_clinical_anamnesis,
                    max_length=12000,
                    rows=6,
                    help_text="Até 12.000 caracteres.",
                ),
                _clinical_field(
                    label="Diagnóstico",
                    control_id="clinical-diagnosis",
                    value=DoctorQueueState.clinical_diagnosis,
                    on_change=DoctorQueueState.update_clinical_diagnosis,
                    max_length=6000,
                    rows=4,
                    help_text="Até 6.000 caracteres. Texto livre nesta etapa.",
                ),
                _clinical_field(
                    label="Conduta e observações",
                    control_id="clinical-conduct-notes",
                    value=DoctorQueueState.clinical_conduct_notes,
                    on_change=DoctorQueueState.update_clinical_conduct_notes,
                    max_length=8000,
                    rows=5,
                    help_text="Até 8.000 caracteres.",
                ),
                rx.flex(
                    rx.cond(
                        DoctorQueueState.clinical_is_dirty,
                        rx.button(
                            "Descartar alterações",
                            type="button",
                            variant="ghost",
                            color_scheme="gray",
                            on_click=DoctorQueueState.restore_clinical_snapshot,
                            disabled=DoctorQueueState.is_saving_clinical
                            | DoctorQueueState.is_submitting
                            | DoctorQueueState.is_prescription_submitting,
                        ),
                        rx.fragment(),
                    ),
                    rx.button(
                        "Salvar atendimento",
                        type="submit",
                        color_scheme="teal",
                        high_contrast=True,
                        disabled=~DoctorQueueState.clinical_is_dirty
                        | DoctorQueueState.is_saving_clinical
                        | DoctorQueueState.is_submitting
                        | DoctorQueueState.is_prescription_submitting,
                        loading=DoctorQueueState.is_saving_clinical,
                    ),
                    direction=rx.breakpoints(initial="column-reverse", sm="row"),
                    justify="end",
                    align=rx.breakpoints(initial="stretch", sm="center"),
                    gap="0.5rem",
                    width="100%",
                ),
                spacing="4",
                align="stretch",
                width="100%",
            ),
            no_validate=True,
            on_submit=DoctorQueueState.save_clinical,
            width="100%",
            margin_top="1rem",
        ),
        prescription_panel(),
        clinical_history_panel(),
        class_name="vitta-clinical-workspace",
        width="100%",
    )


def _finish_review_dialog() -> rx.Component:
    """Review the real episode before committing the irreversible finalization."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Revisar finalização do atendimento"),
            rx.dialog.description(
                "Confira o paciente e o registro salvo. A finalização encerra "
                "a edição clínica deste episódio, preservando o histórico.",
                margin_top="0.35rem",
                margin_bottom="1rem",
            ),
            rx.vstack(
                rx.text(
                    DoctorQueueState.active_patient_name,
                    font_weight="800",
                    size="3",
                ),
                rx.hstack(
                    rx.text("Classificação:", font_weight="650", size="2"),
                    priority_badge(
                        DoctorQueueState.active_priority,
                        DoctorQueueState.active_priority_label,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Queixa principal",
                    font_weight="700",
                    size="2",
                    color="var(--vitta-text-muted)",
                ),
                rx.text(
                    DoctorQueueState.clinical_chief_complaint,
                    size="2",
                    white_space="pre-wrap",
                    overflow_wrap="anywhere",
                ),
                rx.text(
                    DoctorQueueState.prescription_count,
                    " prescrição(ões) neste atendimento",
                    size="2",
                    color="var(--vitta-text-muted)",
                ),
                spacing="2",
                align="stretch",
                width="100%",
                padding="1rem",
                background="var(--vitta-surface-muted)",
                border_radius="var(--vitta-radius-control)",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Voltar ao atendimento",
                        type="button",
                        variant="outline",
                        color_scheme="gray",
                        disabled=DoctorQueueState.is_submitting,
                        auto_focus=True,
                    )
                ),
                rx.button(
                    "Confirmar finalização",
                    type="button",
                    color_scheme="teal",
                    high_contrast=True,
                    on_click=DoctorQueueState.begin_finish_review,
                    disabled=DoctorQueueState.is_submitting
                    | DoctorQueueState.is_saving_clinical
                    | DoctorQueueState.is_prescription_submitting
                    | DoctorQueueState.clinical_is_dirty,
                    loading=DoctorQueueState.is_submitting,
                ),
                direction=rx.breakpoints(initial="column-reverse", sm="row"),
                justify="end",
                gap="0.65rem",
                width="100%",
                margin_top="1.25rem",
            ),
            class_name="vitta-dialog-content",
            max_width="38rem",
        ),
        open=DoctorQueueState.finish_dialog_open,
        on_open_change=DoctorQueueState.set_finish_dialog_open,
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
                rx.cond(
                    DoctorQueueState.active_is_scheduled,
                    rx.box(
                        rx.hstack(
                            rx.icon("calendar_clock", size=17),
                            rx.box(
                                rx.text(
                                    "Consulta agendada",
                                    font_weight="750",
                                    size="2",
                                ),
                                rx.text(
                                    DoctorQueueState.active_professional_name,
                                    " · ",
                                    DoctorQueueState.active_scheduled_at,
                                    size="1",
                                    color="var(--vitta-text-muted)",
                                    class_name="vitta-tabular",
                                    margin_top="0.15rem",
                                ),
                            ),
                            spacing="3",
                            align="center",
                        ),
                        class_name="vitta-info-strip",
                    ),
                    rx.fragment(),
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
                        white_space="pre-wrap",
                        margin_top="0.35rem",
                    ),
                    width="100%",
                    padding="1rem",
                    background="var(--vitta-surface-muted)",
                    border_radius="var(--vitta-radius-control)",
                ),
                clinical_care_form(),
                rx.button(
                    "Revisar e finalizar",
                    type="button",
                    color_scheme="teal",
                    high_contrast=True,
                    min_height="3rem",
                    width=rx.breakpoints(initial="100%", sm="auto"),
                    on_click=DoctorQueueState.begin_finish_review,
                    disabled=DoctorQueueState.is_submitting
                    | DoctorQueueState.is_saving_clinical
                    | DoctorQueueState.is_prescription_submitting
                    | DoctorQueueState.clinical_is_dirty,
                    loading=DoctorQueueState.is_submitting,
                ),
                _finish_review_dialog(),
                rx.cond(
                    DoctorQueueState.clinical_is_dirty,
                    rx.text(
                        "Salve ou descarte as alterações clínicas antes de finalizar.",
                        size="1",
                        color="var(--vitta-warning)",
                        role="status",
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                align="stretch",
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
                        disabled=DoctorQueueState.is_submitting,
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

