"""Reflex states for the patient reception queue capability."""

from typing import Any, TypedDict

import reflex as rx

from vitta_one.appointment_scheduling.temporal import format_clinic_datetime
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.state import AuthState
from vitta_one.clinical_care.application import (
    doctor_get_active_record,
    doctor_list_active_patient_history,
    doctor_save_active_record,
)
from vitta_one.clinical_care.service import (
    ClinicalCareAuthorizationError,
    ClinicalCareNotFoundError,
    ClinicalCareTransitionError,
    ClinicalCareValidationError,
)
from vitta_one.clinical_prescription.application import (
    doctor_add_prescription_item,
    doctor_create_prescription,
    doctor_delete_prescription,
    doctor_list_current_prescriptions,
    doctor_remove_prescription_item,
    doctor_update_prescription_item,
    doctor_update_prescription_notes,
)
from vitta_one.clinical_prescription.service import (
    PrescriptionAuthorizationError,
    PrescriptionConflictError,
    PrescriptionNotFoundError,
    PrescriptionTransitionError,
    PrescriptionValidationError,
)
from vitta_one.patient_queue.application import (
    doctor_active_queue_entry,
    doctor_claim_next,
    doctor_finish,
    doctor_waiting_count,
    reception_create_patient,
    reception_get_patient_identity,
    reception_search_patients,
    reception_enqueue,
    reception_find_patient,
    reception_update_patient,
    reception_list_queue,
    reception_reassess,
    reception_withdraw,
)
from vitta_one.patient_portal.application import (
    reception_get_patient_portal_status,
    reception_issue_patient_invitation,
)
from vitta_one.patient_portal.service import PatientPortalError
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
    phone: str


class PatientUpdateFormData(TypedDict):
    name: str
    phone: str


class PatientPortalInviteFormData(TypedDict):
    email: str
    consent_confirmed: str


class PatientSearchFormData(TypedDict):
    cpf: str


class PatientSearchResultRow(TypedDict):
    id: int
    name: str
    phone: str


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


class PrescriptionItemRow(TypedDict):
    id: int
    prescription_id: int
    medication_or_item: str
    instructions: str
    notes: str


class PrescriptionRow(TypedDict):
    id: int
    clinical_care_record_id: int
    consultation_id: int | None
    general_notes: str
    created_at: str
    items: list[PrescriptionItemRow]
    item_count: int


class ClinicalHistoryRow(TypedDict):
    record_id: int
    consultation_id: int | None
    professional_name: str
    scheduled_at: str
    completed_at: str
    chief_complaint: str
    anamnesis: str
    diagnosis: str
    conduct_notes: str
    prescriptions: list[PrescriptionRow]
    prescription_count: int


def _format_patient_contact(value: str | None) -> str:
    digits = "".join(character for character in str(value or "") if character.isdigit())
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return "Telefone não informado"


def _serialize_prescription_item(item) -> PrescriptionItemRow:
    return {
        "id": item.id,
        "prescription_id": item.prescription_id,
        "medication_or_item": item.medication_or_item,
        "instructions": item.instructions,
        "notes": item.notes,
    }


def _serialize_prescription(item) -> PrescriptionRow:
    serialized_items = [
        _serialize_prescription_item(child) for child in item.items
    ]
    return {
        "id": item.id,
        "clinical_care_record_id": item.clinical_care_record_id,
        "consultation_id": item.consultation_id,
        "general_notes": item.general_notes,
        "created_at": format_clinic_datetime(item.created_at),
        "items": serialized_items,
        "item_count": len(serialized_items),
    }


def _serialize_history_item(item) -> ClinicalHistoryRow:
    prescriptions = [_serialize_prescription(value) for value in item.prescriptions]
    return {
        "record_id": item.record_id,
        "consultation_id": item.consultation_id,
        "professional_name": item.professional_name,
        "scheduled_at": format_clinic_datetime(item.scheduled_at),
        "completed_at": format_clinic_datetime(item.completed_at),
        "chief_complaint": item.chief_complaint,
        "anamnesis": item.anamnesis,
        "diagnosis": item.diagnosis,
        "conduct_notes": item.conduct_notes,
        "prescriptions": prescriptions,
        "prescription_count": len(prescriptions),
    }


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
    selected_patient_phone: str = ""
    selected_patient_portal_status: str = ""
    is_loading_queue: bool = False
    is_submitting: bool = False
    error_message: str = ""
    success_message: str = ""
    quick_search_query: str = ""
    quick_search_results: list[PatientSearchResultRow] = []
    quick_search_error: str = ""
    is_quick_searching: bool = False

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
        self.selected_patient_phone = ""
        self.selected_patient_portal_status = ""
        self.quick_search_query = ""
        self.quick_search_results = []
        self.quick_search_error = ""
        self.is_quick_searching = False
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
    def update_quick_search_query(self, value: str) -> None:
        self.quick_search_query = str(value or "")[:100]
        self.quick_search_results = []
        self.quick_search_error = ""

    @rx.event
    async def quick_search_patients(self, form_data: dict[str, str]):
        self.quick_search_query = str(
            form_data.get("query", self.quick_search_query) or ""
        )[:100]
        self.quick_search_results = []
        self.quick_search_error = ""
        query = self.quick_search_query.strip()
        if len(query) < 2:
            self.quick_search_error = "Digite ao menos 2 caracteres para buscar."
            return

        self.is_quick_searching = True
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                results = reception_search_patients(
                    db, token=token, query=query, limit=8
                )
            self.quick_search_results = [
                {
                    "id": item.id,
                    "name": item.name,
                    "phone": _format_patient_contact(item.phone),
                }
                for item in results
            ]
            if not self.quick_search_results:
                self.quick_search_error = "Nenhum paciente localizado."
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            self._clear_sensitive_view()
            if isinstance(exc, AuthenticationRequiredError):
                yield rx.redirect("/login")
            else:
                yield rx.redirect("/acesso-negado")
        except Exception:
            self.quick_search_error = (
                "Não foi possível buscar pacientes agora. Tente novamente."
            )
            self.quick_search_results = []
        finally:
            self.is_quick_searching = False
            yield

    @rx.event
    async def select_quick_search_patient(self, patient_id: int):
        try:
            token = await self._token()
            with rx.session() as db:
                patient = reception_get_patient_identity(
                    db, token=token, patient_id=patient_id
                )
            if patient is None:
                self.quick_search_error = "Este cadastro não está disponível."
                self.quick_search_results = []
                return
            self.selected_patient_id = patient.id
            self.selected_patient_name = patient.name
            self.selected_patient_phone = patient.phone or ""
            with rx.session() as db:
                portal_status = reception_get_patient_portal_status(
                    db, token=token, patient_id=patient.id
                )
            self.selected_patient_portal_status = portal_status.label
            self.quick_search_query = ""
            self.quick_search_results = []
            self.quick_search_error = ""
            return rx.redirect("/recepcao/pacientes")
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            self._clear_sensitive_view()
            if isinstance(exc, AuthenticationRequiredError):
                return rx.redirect("/login")
            return rx.redirect("/acesso-negado")
        except Exception:
            self.quick_search_error = (
                "Não foi possível abrir o cadastro agora. Tente novamente."
            )
            return

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
                    phone=str(form_data.get("phone", "")),
                )
            if patient.id is None:
                raise RuntimeError("Paciente criado sem identificador.")
            self.selected_patient_id = patient.id
            self.selected_patient_name = patient.name
            self.selected_patient_phone = patient.phone or ""
            self.selected_patient_portal_status = "Sem acesso ao portal"
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
                self.selected_patient_phone = patient.phone or ""
                with rx.session() as db:
                    portal_status = reception_get_patient_portal_status(
                        db, token=token, patient_id=patient.id
                    )
                self.selected_patient_portal_status = portal_status.label
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
        self.selected_patient_phone = ""
        self.selected_patient_portal_status = ""
        self._clear_feedback()

    @rx.event
    def update_selected_patient_name(self, value: str) -> None:
        self.selected_patient_name = str(value or "")[:160]

    @rx.event
    def update_selected_patient_phone(self, value: str) -> None:
        self.selected_patient_phone = str(value or "")[:20]

    @rx.event
    async def update_selected_patient(self, form_data: PatientUpdateFormData):
        if not self.selected_patient_id:
            self.error_message = "Localize um paciente antes de atualizar o cadastro."
            return
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                patient = reception_update_patient(
                    db,
                    token=token,
                    patient_id=self.selected_patient_id,
                    name=str(form_data.get("name", "")),
                    phone=str(form_data.get("phone", "")),
                )
            self.selected_patient_name = patient.name
            self.selected_patient_phone = patient.phone or ""
            self.success_message = "Cadastro operacional atualizado."
        except (PatientValidationError, PatientPortalError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível atualizar o cadastro agora. Tente novamente."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def issue_patient_portal_invitation(self, form_data: PatientPortalInviteFormData):
        if not self.selected_patient_id:
            self.error_message = "Localize um paciente antes de enviar o convite."
            return
        consent = str(form_data.get("consent_confirmed", "")).casefold() in {
            "on", "true", "1", "yes"
        }
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                status, _delivery = reception_issue_patient_invitation(
                    db,
                    token=token,
                    patient_id=self.selected_patient_id,
                    email=str(form_data.get("email", "")),
                    consent_confirmed=consent,
                )
            self.selected_patient_portal_status = status.label
            if status.state == "ACCEPTED":
                self.success_message = status.label
            else:
                self.error_message = status.label
        except PatientPortalError as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível preparar o convite agora. Tente novamente."
        finally:
            self.is_submitting = False
            yield

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
    """Doctor queue, clinical-record and prescription state."""

    waiting_count: int = 0
    has_active: bool = False
    active_entry_id: int = 0
    active_consultation_id: int = 0
    active_patient_name: str = ""
    active_symptoms: str = ""
    active_priority: str = ""
    active_priority_label: str = ""
    active_called_at: str = ""
    active_is_scheduled: bool = False
    active_scheduled_at: str = ""
    active_professional_name: str = ""

    clinical_record_id: int = 0
    clinical_chief_complaint: str = ""
    clinical_anamnesis: str = ""
    clinical_diagnosis: str = ""
    clinical_conduct_notes: str = ""
    persisted_chief_complaint: str = ""
    persisted_anamnesis: str = ""
    persisted_diagnosis: str = ""
    persisted_conduct_notes: str = ""
    clinical_history: list[ClinicalHistoryRow] = []
    clinical_history_page: int = 1
    clinical_history_total_pages: int = 1
    clinical_history_total_count: int = 0

    prescriptions: list[PrescriptionRow] = []
    is_prescription_submitting: bool = False

    new_prescription_dialog_open: bool = False
    new_prescription_medication: str = ""
    new_prescription_instructions: str = ""
    new_prescription_item_notes: str = ""
    new_prescription_general_notes: str = ""

    prescription_item_dialog_open: bool = False
    prescription_item_mode: str = "add"
    prescription_target_id: int = 0
    prescription_item_id: int = 0
    prescription_item_medication: str = ""
    prescription_item_instructions: str = ""
    prescription_item_notes: str = ""

    prescription_notes_dialog_open: bool = False
    prescription_notes_target_id: int = 0
    prescription_general_notes: str = ""

    delete_prescription_dialog_open: bool = False
    delete_prescription_id: int = 0

    remove_prescription_item_dialog_open: bool = False
    remove_prescription_id: int = 0
    remove_prescription_item_id: int = 0
    remove_prescription_item_name: str = ""

    is_loading: bool = False
    is_submitting: bool = False
    is_saving_clinical: bool = False
    finish_dialog_open: bool = False
    error_message: str = ""
    success_message: str = ""

    @rx.var
    def prescription_count(self) -> int:
        return len(self.prescriptions)

    @rx.var
    def has_clinical_record(self) -> bool:
        return self.has_active and self.clinical_record_id > 0

    @rx.var
    def clinical_is_dirty(self) -> bool:
        return self.has_clinical_record and (
            self.clinical_chief_complaint != self.persisted_chief_complaint
            or self.clinical_anamnesis != self.persisted_anamnesis
            or self.clinical_diagnosis != self.persisted_diagnosis
            or self.clinical_conduct_notes != self.persisted_conduct_notes
        )

    @rx.var
    def can_previous_clinical_history_page(self) -> bool:
        return self.clinical_history_page > 1

    @rx.var
    def can_next_clinical_history_page(self) -> bool:
        return self.clinical_history_page < self.clinical_history_total_pages

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear_feedback(self) -> None:
        self.error_message = ""
        self.success_message = ""

    def _reset_new_prescription(self) -> None:
        self.new_prescription_dialog_open = False
        self.new_prescription_medication = ""
        self.new_prescription_instructions = ""
        self.new_prescription_item_notes = ""
        self.new_prescription_general_notes = ""

    def _reset_prescription_item_dialog(self) -> None:
        self.prescription_item_dialog_open = False
        self.prescription_item_mode = "add"
        self.prescription_target_id = 0
        self.prescription_item_id = 0
        self.prescription_item_medication = ""
        self.prescription_item_instructions = ""
        self.prescription_item_notes = ""

    def _reset_prescription_notes_dialog(self) -> None:
        self.prescription_notes_dialog_open = False
        self.prescription_notes_target_id = 0
        self.prescription_general_notes = ""

    def _reset_delete_prescription(self) -> None:
        self.delete_prescription_dialog_open = False
        self.delete_prescription_id = 0

    def _reset_remove_item(self) -> None:
        self.remove_prescription_item_dialog_open = False
        self.remove_prescription_id = 0
        self.remove_prescription_item_id = 0
        self.remove_prescription_item_name = ""

    def _clear_prescriptions(self) -> None:
        self.prescriptions = []
        self._reset_new_prescription()
        self._reset_prescription_item_dialog()
        self._reset_prescription_notes_dialog()
        self._reset_delete_prescription()
        self._reset_remove_item()
        self.is_prescription_submitting = False

    def _clear_clinical(self) -> None:
        self.clinical_record_id = 0
        self.clinical_chief_complaint = ""
        self.clinical_anamnesis = ""
        self.clinical_diagnosis = ""
        self.clinical_conduct_notes = ""
        self.persisted_chief_complaint = ""
        self.persisted_anamnesis = ""
        self.persisted_diagnosis = ""
        self.persisted_conduct_notes = ""
        self.clinical_history = []
        self.clinical_history_page = 1
        self.clinical_history_total_pages = 1
        self.clinical_history_total_count = 0
        self._clear_prescriptions()

    def _clear_active(self) -> None:
        self.finish_dialog_open = False
        self.has_active = False
        self.active_entry_id = 0
        self.active_consultation_id = 0
        self.active_patient_name = ""
        self.active_symptoms = ""
        self.active_priority = ""
        self.active_priority_label = ""
        self.active_called_at = ""
        self.active_is_scheduled = False
        self.active_scheduled_at = ""
        self.active_professional_name = ""
        self._clear_clinical()

    def _set_active(self, item) -> None:
        self._clear_clinical()
        if item is None:
            self._clear_active()
            return
        self.has_active = True
        self.active_entry_id = item.id
        self.active_consultation_id = item.consultation_id or 0
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

    def _set_clinical_record(self, item) -> None:
        self.clinical_record_id = item.id
        self.clinical_chief_complaint = item.chief_complaint
        self.clinical_anamnesis = item.anamnesis
        self.clinical_diagnosis = item.diagnosis
        self.clinical_conduct_notes = item.conduct_notes
        self.persisted_chief_complaint = item.chief_complaint
        self.persisted_anamnesis = item.anamnesis
        self.persisted_diagnosis = item.diagnosis
        self.persisted_conduct_notes = item.conduct_notes

    def _set_prescriptions(self, items) -> None:
        self.prescriptions = [_serialize_prescription(item) for item in items]

    def _set_clinical_history(self, page) -> None:
        self.clinical_history = [_serialize_history_item(item) for item in page.items]
        self.clinical_history_page = page.page
        self.clinical_history_total_pages = page.total_pages
        self.clinical_history_total_count = page.total_count

    def _load_prescriptions_with_token(self, token: str) -> None:
        if not self.clinical_record_id:
            self.prescriptions = []
            return
        with rx.session() as db:
            items = doctor_list_current_prescriptions(
                db,
                token=token,
                clinical_care_record_id=self.clinical_record_id,
            )
        self._set_prescriptions(items)

    def _load_clinical_with_token(self, token: str, *, page: int = 1) -> None:
        if not self.has_active or not self.active_entry_id:
            self._clear_clinical()
            return
        with rx.session() as db:
            record = doctor_get_active_record(
                db,
                token=token,
                entry_id=self.active_entry_id,
            )
            history = doctor_list_active_patient_history(
                db,
                token=token,
                entry_id=self.active_entry_id,
                page=page,
            )
            prescriptions = doctor_list_current_prescriptions(
                db,
                token=token,
                clinical_care_record_id=record.id,
            )
        self._set_clinical_record(record)
        self._set_clinical_history(history)
        self._set_prescriptions(prescriptions)

    def _load_history_with_token(self, token: str, *, page: int) -> None:
        if not self.has_active or not self.active_entry_id:
            self.clinical_history = []
            self.clinical_history_page = 1
            self.clinical_history_total_pages = 1
            self.clinical_history_total_count = 0
            return
        with rx.session() as db:
            history = doctor_list_active_patient_history(
                db,
                token=token,
                entry_id=self.active_entry_id,
                page=page,
            )
        self._set_clinical_history(history)

    def _load_with_token(self, token: str) -> None:
        with rx.session() as db:
            active = doctor_active_queue_entry(db, token=token)
            count = doctor_waiting_count(db, token=token)
        self._set_active(active)
        self.waiting_count = count
        if self.has_active:
            self._load_clinical_with_token(token, page=1)

    async def _authorization_redirect(self, exc: Exception):
        self.waiting_count = 0
        self._clear_active()
        if isinstance(exc, AuthenticationRequiredError):
            yield rx.redirect("/login")
        else:
            yield rx.redirect("/acesso-negado")

    def _prescription_error(self, exc: Exception) -> None:
        self.error_message = str(exc)

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
        except (
            ClinicalCareAuthorizationError,
            ClinicalCareNotFoundError,
            ClinicalCareTransitionError,
            PrescriptionAuthorizationError,
            PrescriptionNotFoundError,
            PrescriptionTransitionError,
        ) as exc:
            self.error_message = str(exc)
            self._clear_clinical()
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
            if self.has_active:
                self._load_clinical_with_token(token, page=1)
            self.success_message = "Próximo paciente chamado para atendimento."
        except QueueEmptyError:
            self.error_message = "Não há pacientes aguardando neste momento."
            self.waiting_count = 0
        except (
            DoctorAlreadyAttendingError,
            QueueTransitionError,
            QueueOwnershipError,
            ClinicalCareAuthorizationError,
            ClinicalCareNotFoundError,
            ClinicalCareTransitionError,
            PrescriptionAuthorizationError,
            PrescriptionNotFoundError,
            PrescriptionTransitionError,
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
    def update_clinical_chief_complaint(self, value: str) -> None:
        self.clinical_chief_complaint = value

    @rx.event
    def update_clinical_anamnesis(self, value: str) -> None:
        self.clinical_anamnesis = value

    @rx.event
    def update_clinical_diagnosis(self, value: str) -> None:
        self.clinical_diagnosis = value

    @rx.event
    def update_clinical_conduct_notes(self, value: str) -> None:
        self.clinical_conduct_notes = value

    @rx.event
    def restore_clinical_snapshot(self) -> None:
        self.clinical_chief_complaint = self.persisted_chief_complaint
        self.clinical_anamnesis = self.persisted_anamnesis
        self.clinical_diagnosis = self.persisted_diagnosis
        self.clinical_conduct_notes = self.persisted_conduct_notes
        self._clear_feedback()

    @rx.event
    async def save_clinical(self, _form_data: dict[str, Any]):
        self.is_saving_clinical = True
        self._clear_feedback()
        yield
        try:
            if not self.has_clinical_record or not self.active_entry_id:
                raise ClinicalCareNotFoundError(
                    "Não há registro clínico ativo para salvar."
                )
            token = await self._token()
            with rx.session() as db:
                record = doctor_save_active_record(
                    db,
                    token=token,
                    entry_id=self.active_entry_id,
                    chief_complaint=self.clinical_chief_complaint,
                    anamnesis=self.clinical_anamnesis,
                    diagnosis=self.clinical_diagnosis,
                    conduct_notes=self.clinical_conduct_notes,
                )
            self._set_clinical_record(record)
            self.success_message = "Atendimento clínico salvo."
        except (
            ClinicalCareAuthorizationError,
            ClinicalCareNotFoundError,
            ClinicalCareTransitionError,
            ClinicalCareValidationError,
        ) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível salvar o atendimento clínico agora. Tente novamente."
            )
        finally:
            self.is_saving_clinical = False
            yield

    @rx.event
    def open_prescription_print(self, prescription_id: int):
        return rx.redirect(f"/medico/prescricao/{prescription_id}")

    @rx.event
    def begin_new_prescription(self) -> None:
        self._clear_feedback()
        self._reset_prescription_item_dialog()
        self._reset_prescription_notes_dialog()
        self._reset_delete_prescription()
        self._reset_remove_item()
        self.new_prescription_dialog_open = True

    @rx.event
    def set_new_prescription_dialog_open(self, is_open: bool) -> None:
        if self.is_prescription_submitting and not is_open:
            return
        if is_open:
            self.new_prescription_dialog_open = True
        else:
            self._reset_new_prescription()

    @rx.event
    def update_new_prescription_medication(self, value: str) -> None:
        self.new_prescription_medication = value

    @rx.event
    def update_new_prescription_instructions(self, value: str) -> None:
        self.new_prescription_instructions = value

    @rx.event
    def update_new_prescription_item_notes(self, value: str) -> None:
        self.new_prescription_item_notes = value

    @rx.event
    def update_new_prescription_general_notes(self, value: str) -> None:
        self.new_prescription_general_notes = value

    @rx.event
    async def create_prescription(self, _form_data: dict[str, Any]):
        self.is_prescription_submitting = True
        self._clear_feedback()
        yield
        try:
            if not self.clinical_record_id:
                raise PrescriptionNotFoundError(
                    "Não há Atendimento clínico ativo para criar Prescrição."
                )
            token = await self._token()
            with rx.session() as db:
                doctor_create_prescription(
                    db,
                    token=token,
                    clinical_care_record_id=self.clinical_record_id,
                    medication_or_item=self.new_prescription_medication,
                    instructions=self.new_prescription_instructions,
                    notes=self.new_prescription_item_notes,
                    general_notes=self.new_prescription_general_notes,
                )
            self._load_prescriptions_with_token(token)
            self._reset_new_prescription()
            self.success_message = "Prescrição criada."
        except (
            PrescriptionValidationError,
            PrescriptionAuthorizationError,
            PrescriptionTransitionError,
            PrescriptionConflictError,
            PrescriptionNotFoundError,
        ) as exc:
            self._prescription_error(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível criar a Prescrição agora."
        finally:
            self.is_prescription_submitting = False
            yield

    @rx.event
    def begin_add_prescription_item(self, prescription_id: int) -> None:
        self._clear_feedback()
        self._reset_new_prescription()
        self._reset_prescription_notes_dialog()
        self._reset_delete_prescription()
        self._reset_remove_item()
        self.prescription_item_mode = "add"
        self.prescription_target_id = prescription_id
        self.prescription_item_dialog_open = True

    @rx.event
    def begin_edit_prescription_item(
        self,
        prescription_id: int,
        item_id: int,
        medication_or_item: str,
        instructions: str,
        notes: str,
    ) -> None:
        self._clear_feedback()
        self._reset_new_prescription()
        self._reset_prescription_notes_dialog()
        self._reset_delete_prescription()
        self._reset_remove_item()
        self.prescription_item_mode = "edit"
        self.prescription_target_id = prescription_id
        self.prescription_item_id = item_id
        self.prescription_item_medication = medication_or_item
        self.prescription_item_instructions = instructions
        self.prescription_item_notes = notes
        self.prescription_item_dialog_open = True

    @rx.event
    def set_prescription_item_dialog_open(self, is_open: bool) -> None:
        if self.is_prescription_submitting and not is_open:
            return
        if is_open:
            self.prescription_item_dialog_open = True
        else:
            self._reset_prescription_item_dialog()

    @rx.event
    def update_prescription_item_medication(self, value: str) -> None:
        self.prescription_item_medication = value

    @rx.event
    def update_prescription_item_instructions(self, value: str) -> None:
        self.prescription_item_instructions = value

    @rx.event
    def update_prescription_item_notes(self, value: str) -> None:
        self.prescription_item_notes = value

    @rx.event
    async def submit_prescription_item(self, _form_data: dict[str, Any]):
        self.is_prescription_submitting = True
        self._clear_feedback()
        yield
        try:
            if not self.prescription_target_id:
                raise PrescriptionNotFoundError("Selecione uma Prescrição válida.")
            token = await self._token()
            with rx.session() as db:
                if self.prescription_item_mode == "edit":
                    if not self.prescription_item_id:
                        raise PrescriptionNotFoundError(
                            "Selecione um item válido para editar."
                        )
                    doctor_update_prescription_item(
                        db,
                        token=token,
                        prescription_id=self.prescription_target_id,
                        item_id=self.prescription_item_id,
                        medication_or_item=self.prescription_item_medication,
                        instructions=self.prescription_item_instructions,
                        notes=self.prescription_item_notes,
                    )
                    message = "Item da Prescrição atualizado."
                else:
                    doctor_add_prescription_item(
                        db,
                        token=token,
                        prescription_id=self.prescription_target_id,
                        medication_or_item=self.prescription_item_medication,
                        instructions=self.prescription_item_instructions,
                        notes=self.prescription_item_notes,
                    )
                    message = "Item adicionado à Prescrição."
            self._load_prescriptions_with_token(token)
            self._reset_prescription_item_dialog()
            self.success_message = message
        except (
            PrescriptionValidationError,
            PrescriptionAuthorizationError,
            PrescriptionTransitionError,
            PrescriptionConflictError,
            PrescriptionNotFoundError,
        ) as exc:
            self._prescription_error(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível salvar o item da Prescrição agora."
        finally:
            self.is_prescription_submitting = False
            yield

    @rx.event
    def begin_prescription_notes(self, prescription_id: int, general_notes: str) -> None:
        self._clear_feedback()
        self._reset_new_prescription()
        self._reset_prescription_item_dialog()
        self._reset_delete_prescription()
        self._reset_remove_item()
        self.prescription_notes_target_id = prescription_id
        self.prescription_general_notes = general_notes
        self.prescription_notes_dialog_open = True

    @rx.event
    def set_prescription_notes_dialog_open(self, is_open: bool) -> None:
        if self.is_prescription_submitting and not is_open:
            return
        if is_open:
            self.prescription_notes_dialog_open = True
        else:
            self._reset_prescription_notes_dialog()

    @rx.event
    def update_prescription_general_notes(self, value: str) -> None:
        self.prescription_general_notes = value

    @rx.event
    async def save_prescription_notes(self, _form_data: dict[str, Any]):
        self.is_prescription_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                doctor_update_prescription_notes(
                    db,
                    token=token,
                    prescription_id=self.prescription_notes_target_id,
                    general_notes=self.prescription_general_notes,
                )
            self._load_prescriptions_with_token(token)
            self._reset_prescription_notes_dialog()
            self.success_message = "Observações gerais atualizadas."
        except (
            PrescriptionValidationError,
            PrescriptionAuthorizationError,
            PrescriptionTransitionError,
            PrescriptionConflictError,
            PrescriptionNotFoundError,
        ) as exc:
            self._prescription_error(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível salvar as observações agora."
        finally:
            self.is_prescription_submitting = False
            yield

    @rx.event
    def begin_delete_prescription(self, prescription_id: int) -> None:
        self._clear_feedback()
        self._reset_new_prescription()
        self._reset_prescription_item_dialog()
        self._reset_prescription_notes_dialog()
        self._reset_remove_item()
        self.delete_prescription_id = prescription_id
        self.delete_prescription_dialog_open = True

    @rx.event
    def set_delete_prescription_dialog_open(self, is_open: bool) -> None:
        if self.is_prescription_submitting and not is_open:
            return
        if is_open:
            self.delete_prescription_dialog_open = True
        else:
            self._reset_delete_prescription()

    @rx.event
    async def confirm_delete_prescription(self):
        self.is_prescription_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                doctor_delete_prescription(
                    db,
                    token=token,
                    prescription_id=self.delete_prescription_id,
                )
            self._load_prescriptions_with_token(token)
            self._reset_delete_prescription()
            self.success_message = "Prescrição excluída do atendimento em andamento."
        except (
            PrescriptionAuthorizationError,
            PrescriptionTransitionError,
            PrescriptionConflictError,
            PrescriptionNotFoundError,
        ) as exc:
            self._prescription_error(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível excluir a Prescrição agora."
        finally:
            self.is_prescription_submitting = False
            yield

    @rx.event
    def begin_remove_prescription_item(
        self,
        prescription_id: int,
        item_id: int,
        medication_or_item: str,
    ) -> None:
        self._clear_feedback()
        self._reset_new_prescription()
        self._reset_prescription_item_dialog()
        self._reset_prescription_notes_dialog()
        self._reset_delete_prescription()
        self.remove_prescription_id = prescription_id
        self.remove_prescription_item_id = item_id
        self.remove_prescription_item_name = medication_or_item
        self.remove_prescription_item_dialog_open = True

    @rx.event
    def set_remove_prescription_item_dialog_open(self, is_open: bool) -> None:
        if self.is_prescription_submitting and not is_open:
            return
        if is_open:
            self.remove_prescription_item_dialog_open = True
        else:
            self._reset_remove_item()

    @rx.event
    async def confirm_remove_prescription_item(self):
        self.is_prescription_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                doctor_remove_prescription_item(
                    db,
                    token=token,
                    prescription_id=self.remove_prescription_id,
                    item_id=self.remove_prescription_item_id,
                )
            self._load_prescriptions_with_token(token)
            self._reset_remove_item()
            self.success_message = "Item removido da Prescrição."
        except (
            PrescriptionAuthorizationError,
            PrescriptionTransitionError,
            PrescriptionConflictError,
            PrescriptionNotFoundError,
        ) as exc:
            self._prescription_error(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível remover o item agora."
        finally:
            self.is_prescription_submitting = False
            yield

    @rx.event
    async def previous_clinical_history_page(self):
        if not self.can_previous_clinical_history_page:
            return
        self.is_loading = True
        yield
        try:
            token = await self._token()
            self._load_history_with_token(token, page=self.clinical_history_page - 1)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except (
            ClinicalCareAuthorizationError,
            ClinicalCareNotFoundError,
            ClinicalCareTransitionError,
        ) as exc:
            self.error_message = str(exc)
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def next_clinical_history_page(self):
        if not self.can_next_clinical_history_page:
            return
        self.is_loading = True
        yield
        try:
            token = await self._token()
            self._load_history_with_token(token, page=self.clinical_history_page + 1)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except (
            ClinicalCareAuthorizationError,
            ClinicalCareNotFoundError,
            ClinicalCareTransitionError,
        ) as exc:
            self.error_message = str(exc)
        finally:
            self.is_loading = False
            yield

    @rx.event
    def set_finish_dialog_open(self, is_open: bool) -> None:
        if not self.is_submitting:
            self.finish_dialog_open = is_open

    @rx.event
    def cancel_finish_review(self) -> None:
        """Close the controlled review without modifying or finishing the episode."""
        if not self.is_submitting:
            self.finish_dialog_open = False

    @rx.event
    def begin_finish_review(self) -> None:
        self._clear_feedback()
        if not self.has_active or not self.active_entry_id:
            self.error_message = "Chame um paciente antes de finalizar."
            return
        if self.clinical_is_dirty:
            self.error_message = (
                "Salve ou descarte as alterações clínicas antes de revisar."
            )
            return
        if self.is_saving_clinical or self.is_prescription_submitting:
            self.error_message = "Aguarde o salvamento terminar antes de revisar."
            return
        self.finish_dialog_open = True

    @rx.event
    async def finish_active(self):
        self._clear_feedback()
        if self.clinical_is_dirty:
            self.error_message = (
                "Salve ou descarte as alterações clínicas antes de finalizar o atendimento."
            )
            yield
            return
        if self.is_prescription_submitting:
            self.error_message = (
                "Aguarde a operação de Prescrição terminar antes de finalizar."
            )
            yield
            return

        self.is_submitting = True
        yield
        try:
            if not self.has_active or not self.active_entry_id:
                raise QueueTransitionError("Não há atendimento ativo para finalizar.")
            token = await self._token()
            with rx.session() as db:
                doctor_finish(db, token=token, entry_id=self.active_entry_id)
            self._clear_active()
            self.success_message = "Atendimento finalizado e histórico preservado."
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

