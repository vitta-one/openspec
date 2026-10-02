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


class PrintablePrescriptionItemRow(TypedDict):
    medication_or_item: str
    instructions: str
    notes: str


class PrintPrescriptionState(rx.State):
    """Load one prescription by dynamic route after server-side ownership checks."""

    is_loading: bool = False
    loaded: bool = False
    error_message: str = ""
    prescription_id: int = 0
    patient_name: str = ""
    professional_name: str = ""
    registration_identifier: str = ""
    scheduled_at: str = ""
    general_notes: str = ""
    items: list[PrintablePrescriptionItemRow] = []

    def _clear(self) -> None:
        self.loaded = False
        self.error_message = ""
        self.prescription_id = 0
        self.patient_name = ""
        self.professional_name = ""
        self.registration_identifier = ""
        self.scheduled_at = ""
        self.general_notes = ""
        self.items = []

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
            self.prescription_id = prescription_id
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
