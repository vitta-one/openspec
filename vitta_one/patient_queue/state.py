"""Reflex states for the patient reception queue capability."""

from typing import TypedDict

import reflex as rx

from vitta_one.appointment_scheduling.temporal import format_clinic_datetime
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.state import AuthState
from vitta_one.patient_queue.application import (
    doctor_active_queue_entry,
    doctor_claim_next,
    doctor_finish,
    doctor_waiting_count,
    reception_create_patient,
    reception_enqueue,
    reception_find_patient,
    reception_list_queue,
    reception_reassess,
    reception_withdraw,
)
from vitta_one.patient_queue.service import (
    DoctorAlreadyAttendingError,
    PatientAlreadyExistsError,
    PatientValidationError,
    QueueEmptyError,
    QueueOwnershipError,
    QueueTransitionError,
    QueueValidationError,
)


class PatientFormData(TypedDict):
    name: str
    cpf: str


class PatientSearchFormData(TypedDict):
    cpf: str


class QueueFormData(TypedDict):
    symptoms: str
    priority: str


class ReassessFormData(TypedDict):
    symptoms: str
    priority: str


class WithdrawFormData(TypedDict):
    reason: str


class QueueRow(TypedDict):
    id: int
    patient_name: str
    symptoms: str
    priority: str
    priority_label: str
    entered_at: str
    is_scheduled: bool
    scheduled_at: str
    professional_name: str


def _serialize_queue_item(item) -> QueueRow:
    return {
        "id": item.id,
        "patient_name": item.patient_name,
        "symptoms": item.symptoms,
        "priority": item.priority.value,
        "priority_label": item.priority.label,
        "entered_at": item.entered_at.strftime("%H:%M UTC"),
        "is_scheduled": item.consultation_id is not None,
        "scheduled_at": (
            format_clinic_datetime(item.scheduled_at) if item.scheduled_at else ""
        ),
        "professional_name": item.professional_name or "",
    }


class ReceptionQueueState(rx.State):
    """Reception-only UI state; every data operation revalidates RBAC server-side."""

    queue_rows: list[QueueRow] = []
    selected_patient_id: int = 0
    selected_patient_name: str = ""
    is_loading_queue: bool = False
    is_submitting: bool = False
    error_message: str = ""
    success_message: str = ""

    reassess_entry_id: int = 0
    reassess_patient_name: str = ""
    reassess_symptoms: str = ""
    reassess_priority: str = "VERDE"

    withdraw_entry_id: int = 0
    withdraw_patient_name: str = ""
    withdraw_is_scheduled: bool = False

    @rx.var
    def has_queue(self) -> bool:
        return bool(self.queue_rows)

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear_feedback(self) -> None:
        self.error_message = ""
        self.success_message = ""

    def _reset_reassess(self) -> None:
        self.reassess_entry_id = 0
        self.reassess_patient_name = ""
        self.reassess_symptoms = ""
        self.reassess_priority = "VERDE"

    def _reset_withdraw(self) -> None:
        self.withdraw_entry_id = 0
        self.withdraw_patient_name = ""
        self.withdraw_is_scheduled = False

    def _clear_sensitive_view(self) -> None:
        self.queue_rows = []
        self.selected_patient_id = 0
        self.selected_patient_name = ""
        self._reset_reassess()
        self._reset_withdraw()

    def _load_queue_with_token(self, token: str) -> None:
        with rx.session() as db:
            items = reception_list_queue(db, token=token)
        self.queue_rows = [_serialize_queue_item(item) for item in items]

    async def _authorization_redirect(self, exc: Exception):
        self._clear_sensitive_view()
        if isinstance(exc, AuthenticationRequiredError):
            yield rx.redirect("/login")
        else:
            yield rx.redirect("/acesso-negado")

    @rx.event
    async def load(self):
        """Load the active queue after revalidating the receptionist session."""
        self.is_loading_queue = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            self._load_queue_with_token(token)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível carregar a fila agora. Atualize a página e tente novamente."
            )
            self.queue_rows = []
        finally:
            self.is_loading_queue = False
            yield

    @rx.event
    async def create_patient(self, form_data: PatientFormData):
        """Create and select a patient for the next queue-entry operation."""
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                patient = reception_create_patient(
                    db,
                    token=token,
                    name=str(form_data.get("name", "")),
                    cpf=str(form_data.get("cpf", "")),
                )
            if patient.id is None:
                raise RuntimeError("Paciente criado sem identificador.")
            self.selected_patient_id = patient.id
            self.selected_patient_name = patient.name
            self.success_message = "Paciente cadastrado e selecionado para a fila."
        except PatientAlreadyExistsError:
            self.error_message = (
                "Este CPF já está cadastrado. Localize o paciente existente para continuar."
            )
        except PatientValidationError as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível cadastrar o paciente agora. Tente novamente."
            )
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def find_patient(self, form_data: PatientSearchFormData):
        """Select an existing patient by CPF after server-side validation."""
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                patient = reception_find_patient(
                    db, token=token, cpf=str(form_data.get("cpf", ""))
                )
            if patient is None or patient.id is None:
                self.error_message = (
                    "Paciente não encontrado. Confira o CPF ou faça um novo cadastro."
                )
                self.selected_patient_id = 0
                self.selected_patient_name = ""
            else:
                self.selected_patient_id = patient.id
                self.selected_patient_name = patient.name
                self.success_message = "Paciente localizado e selecionado."
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível localizar o paciente agora. Tente novamente."
            )
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def clear_patient_selection(self) -> None:
        self.selected_patient_id = 0
        self.selected_patient_name = ""
        self._clear_feedback()

    @rx.event
    async def enqueue(self, form_data: QueueFormData):
        """Create a waiting queue entry for the currently selected patient."""
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if not self.selected_patient_id:
                raise QueueValidationError(
                    "Localize ou cadastre um paciente antes de colocá-lo na fila."
                )
            token = await self._token()
            with rx.session() as db:
                reception_enqueue(
                    db,
                    token=token,
                    patient_id=self.selected_patient_id,
                    symptoms=str(form_data.get("symptoms", "")),
                    priority=str(form_data.get("priority", "")),
                )
            self._load_queue_with_token(token)
            self.success_message = "Paciente incluído na fila."
            self.selected_patient_id = 0
            self.selected_patient_name = ""
        except QueueValidationError as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível incluir o paciente na fila agora. Tente novamente."
            )
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def begin_reassess(
        self, entry_id: int, patient_name: str, symptoms: str, priority: str
    ) -> None:
        self._clear_feedback()
        self._reset_withdraw()
        self.reassess_entry_id = entry_id
        self.reassess_patient_name = patient_name
        self.reassess_symptoms = symptoms
        self.reassess_priority = priority

    @rx.event
    def update_reassess_symptoms(self, value: str) -> None:
        self.reassess_symptoms = value

    @rx.event
    def update_reassess_priority(self, value: str) -> None:
        self.reassess_priority = value

    @rx.event
    def cancel_reassess(self) -> None:
        self._reset_reassess()

    @rx.event
    async def reassess(self, form_data: ReassessFormData):
        """Persist a manual reassessment only if the entry is still waiting."""
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if not self.reassess_entry_id:
                raise QueueTransitionError("Selecione uma entrada aguardando.")
            token = await self._token()
            with rx.session() as db:
                reception_reassess(
                    db,
                    token=token,
                    entry_id=self.reassess_entry_id,
                    symptoms=str(form_data.get("symptoms", "")),
                    priority=str(form_data.get("priority", "")),
                )
            self._load_queue_with_token(token)
            self._reset_reassess()
            self.success_message = "Reavaliação registrada e fila reordenada."
        except (QueueValidationError, QueueTransitionError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível registrar a reavaliação agora. Tente novamente."
            )
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def begin_withdraw(
        self,
        entry_id: int,
        patient_name: str,
        is_scheduled: bool,
    ) -> None:
        self._clear_feedback()
        self._reset_reassess()
        self.withdraw_entry_id = entry_id
        self.withdraw_patient_name = patient_name
        self.withdraw_is_scheduled = is_scheduled

    @rx.event
    def cancel_withdraw(self) -> None:
        self._reset_withdraw()

    @rx.event
    async def withdraw(self, form_data: WithdrawFormData):
        """Confirm a logical queue withdrawal without deleting history."""
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if not self.withdraw_entry_id:
                raise QueueTransitionError("Selecione uma entrada aguardando.")
            token = await self._token()
            with rx.session() as db:
                reception_withdraw(
                    db,
                    token=token,
                    entry_id=self.withdraw_entry_id,
                    reason=str(form_data.get("reason", "")),
                )
            self._load_queue_with_token(token)
            from vitta_one.appointment_scheduling.state import ReceptionAgendaState

            agenda_state = await self.get_state(ReceptionAgendaState)
            agenda_state._load_with_token(token)
            self._reset_withdraw()
            self.success_message = "Paciente retirado da fila; o histórico foi preservado."
        except (QueueValidationError, QueueTransitionError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível retirar o paciente da fila agora. Tente novamente."
            )
        finally:
            self.is_submitting = False
            yield


class DoctorQueueState(rx.State):
    """Doctor-only queue state with server-side role and ownership checks."""

    waiting_count: int = 0
    has_active: bool = False
    active_entry_id: int = 0
    active_patient_name: str = ""
    active_symptoms: str = ""
    active_priority: str = ""
    active_priority_label: str = ""
    active_called_at: str = ""
    active_is_scheduled: bool = False
    active_scheduled_at: str = ""
    active_professional_name: str = ""
    is_loading: bool = False
    is_submitting: bool = False
    error_message: str = ""
    success_message: str = ""

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear_feedback(self) -> None:
        self.error_message = ""
        self.success_message = ""

    def _clear_active(self) -> None:
        self.has_active = False
        self.active_entry_id = 0
        self.active_patient_name = ""
        self.active_symptoms = ""
        self.active_priority = ""
        self.active_priority_label = ""
        self.active_called_at = ""
        self.active_is_scheduled = False
        self.active_scheduled_at = ""
        self.active_professional_name = ""

    def _set_active(self, item) -> None:
        if item is None:
            self._clear_active()
            return
        self.has_active = True
        self.active_entry_id = item.id
        self.active_patient_name = item.patient_name
        self.active_symptoms = item.symptoms
        self.active_priority = item.priority.value
        self.active_priority_label = item.priority.label
        self.active_called_at = (
            item.called_at.strftime("%H:%M UTC") if item.called_at else ""
        )
        self.active_is_scheduled = item.consultation_id is not None
        self.active_scheduled_at = (
            format_clinic_datetime(item.scheduled_at) if item.scheduled_at else ""
        )
        self.active_professional_name = item.professional_name or ""

    def _load_with_token(self, token: str) -> None:
        with rx.session() as db:
            active = doctor_active_queue_entry(db, token=token)
            count = doctor_waiting_count(db, token=token)
        self._set_active(active)
        self.waiting_count = count

    async def _authorization_redirect(self, exc: Exception):
        self.waiting_count = 0
        self._clear_active()
        if isinstance(exc, AuthenticationRequiredError):
            yield rx.redirect("/login")
        else:
            yield rx.redirect("/acesso-negado")

    @rx.event
    async def load(self):
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            self._load_with_token(token)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível carregar a fila médica agora. Atualize a página."
            )
            self.waiting_count = 0
            self._clear_active()
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def claim_next(self):
        """Claim exactly one eligible waiting entry after server-side authorization."""
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                item = doctor_claim_next(db, token=token)
                count = doctor_waiting_count(db, token=token)
            self._set_active(item)
            self.waiting_count = count
            self.success_message = "Próximo paciente chamado para atendimento."
        except QueueEmptyError:
            self.error_message = "Não há pacientes aguardando neste momento."
            self.waiting_count = 0
        except (
            DoctorAlreadyAttendingError,
            QueueTransitionError,
            QueueOwnershipError,
        ) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível chamar o próximo paciente agora. Tente novamente."
            )
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def finish_active(self):
        """Finish only the active queue entry owned by the authenticated doctor."""
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if not self.has_active or not self.active_entry_id:
                raise QueueTransitionError("Não há atendimento ativo para finalizar.")
            token = await self._token()
            with rx.session() as db:
                doctor_finish(db, token=token, entry_id=self.active_entry_id)
            self._clear_active()
            self.success_message = "Atendimento operacional finalizado."
            with rx.session() as db:
                self.waiting_count = doctor_waiting_count(db, token=token)
        except (QueueTransitionError, QueueOwnershipError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível finalizar o atendimento agora. Tente novamente."
            )
        finally:
            self.is_submitting = False
            yield
