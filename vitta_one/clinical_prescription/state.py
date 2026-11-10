"""Protected printable-prescription state for the doctor author."""

from typing import TypedDict

import reflex as rx

from vitta_one.appointment_scheduling.temporal import format_clinic_datetime
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.state import AuthState
from vitta_one.clinical_prescription.application import doctor_get_printable_prescription
from vitta_one.clinical_prescription.service import (
    PrescriptionAuthorizationError,
    PrescriptionNotFoundError,
    PrescriptionTransitionError,
)
from vitta_one.digital_signature.application import doctor_signed_document_url
from vitta_one.digital_signature.service import (
    SignatureAuthorizationError,
    SignatureError,
    SignatureNotConfiguredError,
    SignatureNotFoundError,
    get_signature,
)
from vitta_one.integrations.zapsign import ZapSignUnavailableError


class PrintablePrescriptionItemRow(TypedDict):
    medication_or_item: str
    instructions: str
    notes: str


class PrintPrescriptionState(rx.State):
    """Load one prescription by dynamic route after server-side ownership checks."""

    is_loading: bool = False
    loaded: bool = False
    error_message: str = ""
    loaded_prescription_id: int = 0
    patient_name: str = ""
    professional_name: str = ""
    registration_identifier: str = ""
    scheduled_at: str = ""
    general_notes: str = ""
    items: list[PrintablePrescriptionItemRow] = []
    signature_status: str = "NOT_SENT"
    signature_status_label: str = "Não enviada para assinatura"
    can_open_signed_document: bool = False

    def _clear(self) -> None:
        self.loaded = False
        self.error_message = ""
        self.loaded_prescription_id = 0
        self.patient_name = ""
        self.professional_name = ""
        self.registration_identifier = ""
        self.scheduled_at = ""
        self.general_notes = ""
        self.items = []
        self.signature_status = "NOT_SENT"
        self.signature_status_label = "Não enviada para assinatura"
        self.can_open_signed_document = False

    @rx.event
    async def load(self):
        self.is_loading = True
        self._clear()
        yield
        try:
            raw_id = str(self.router.page.params.get("prescription_id", "")).strip()
            if not raw_id.isdigit() or int(raw_id) <= 0:
                raise PrescriptionNotFoundError("A Prescrição solicitada não está disponível.")
            prescription_id = int(raw_id)
            auth = await self.get_state(AuthState)
            with rx.session() as db:
                view = doctor_get_printable_prescription(
                    db,
                    token=auth.session_token,
                    prescription_id=prescription_id,
                )
                signature = get_signature(db, prescription_id=prescription_id)
            self.loaded_prescription_id = prescription_id
            self.patient_name = view.patient_name
            self.professional_name = view.professional_name
            self.registration_identifier = view.registration_identifier
            self.scheduled_at = format_clinic_datetime(view.scheduled_at)
            self.general_notes = view.prescription.general_notes
            self.items = [
                {
                    "medication_or_item": item.medication_or_item,
                    "instructions": item.instructions,
                    "notes": item.notes,
                }
                for item in view.prescription.items
            ]
            if signature is not None:
                self.signature_status = signature.status
                self.signature_status_label = {
                    "CREATING": "Preparando envio para assinatura",
                    "PENDING": "Aguardando assinatura digital",
                    "SIGNED": "Documento assinado digitalmente",
                    "REFUSED": "Assinatura recusada",
                    "EXPIRED": "Solicitação de assinatura expirada",
                    "CANCELLED": "Solicitação de assinatura cancelada",
                    "RECONCILIATION_REQUIRED": "Envio pendente de verificação",
                }.get(signature.status, "Status da assinatura indisponível")
                self.can_open_signed_document = signature.can_open_signed_document
            self.loaded = True
        except AuthenticationRequiredError:
            self._clear()
            yield rx.redirect("/login")
        except (RoleForbiddenError, PrescriptionAuthorizationError):
            self._clear()
            yield rx.redirect("/acesso-negado")
        except (PrescriptionNotFoundError, PrescriptionTransitionError) as exc:
            self.error_message = str(exc)
        except Exception:
            self.error_message = "Não foi possível abrir esta Prescrição agora."
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def open_signed_document(self):
        self.error_message = ""
        try:
            if not self.loaded_prescription_id:
                raise SignatureNotFoundError("O documento assinado ainda não está disponível.")
            auth = await self.get_state(AuthState)
            with rx.session() as db:
                url = doctor_signed_document_url(
                    db,
                    token=auth.session_token,
                    prescription_id=self.loaded_prescription_id,
                )
            yield rx.redirect(url)
        except AuthenticationRequiredError:
            self._clear()
            yield rx.redirect("/login")
        except (RoleForbiddenError, SignatureAuthorizationError):
            self._clear()
            yield rx.redirect("/acesso-negado")
        except (
            SignatureError,
            SignatureNotConfiguredError,
            SignatureNotFoundError,
            ZapSignUnavailableError,
        ) as exc:
            self.error_message = str(exc)
        except Exception:
            self.error_message = "Não foi possível abrir o documento assinado agora."

