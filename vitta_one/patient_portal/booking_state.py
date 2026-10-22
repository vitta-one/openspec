"""Patient-controlled appointment booking with server-authorized option refreshes."""
from datetime import datetime
from typing import TypedDict

import reflex as rx

from vitta_one.appointment_scheduling.application import (
    patient_get_booking_options, patient_schedule_own_consultation,
)
from vitta_one.appointment_scheduling.service import (
    SchedulingConflictError, SchedulingNotFoundError, SchedulingValidationError,
)
from vitta_one.appointment_scheduling.temporal import format_clinic_datetime
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.state import AuthState


class BookingSpecialtyRow(TypedDict):
    value: str
    label: str


class BookingDoctorRow(TypedDict):
    value: str
    label: str


class BookingSlotRow(TypedDict):
    id: int
    date: str
    hour: str
    label: str


class BookingDayGroup(TypedDict):
    date: str
    slots: list[BookingSlotRow]


class BookingDayOption(TypedDict):
    value: str
    label: str


_WEEKDAYS_PT = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
                "sexta-feira", "sábado", "domingo")


def available_booking_days(rows: list[BookingSlotRow]) -> list[BookingDayOption]:
    """Build a concise picker of only dates with actual free appointments."""
    options: list[BookingDayOption] = []
    for group in group_booking_slots(rows):
        date_label = group["date"]
        weekday = _WEEKDAYS_PT[datetime.strptime(date_label, "%d/%m/%Y").weekday()]
        quantity = len(group["slots"])
        suffix = "horário disponível" if quantity == 1 else "horários disponíveis"
        options.append({"value": date_label,
                        "label": f"{weekday.capitalize()}, {date_label} · {quantity} {suffix}"})
    return options


def group_booking_slots(rows: list[BookingSlotRow]) -> list[BookingDayGroup]:
    days: dict[str, list[BookingSlotRow]] = {}
    for row in rows:
        days.setdefault(row["date"], []).append(row)
    return [{"date": date, "slots": slots} for date, slots in days.items()]


class PatientBookingState(rx.State):
    specialties: list[BookingSpecialtyRow] = []
    doctors: list[BookingDoctorRow] = []
    slots: list[BookingSlotRow] = []
    selected_specialty: str = "__none__"
    selected_doctor: str = "__none__"
    selected_date: str = "__none__"
    selected_slot_id: int = 0
    selected_slot_label: str = ""
    selected_doctor_name: str = ""
    confirmation_open: bool = False
    booked: bool = False
    booked_description: str = ""
    error_message: str = ""
    success_message: str = ""
    is_loading: bool = False
    is_submitting: bool = False

    @rx.var
    def slot_groups(self) -> list[BookingDayGroup]:
        return group_booking_slots(self.slots)

    @rx.var
    def available_days(self) -> list[BookingDayOption]:
        return available_booking_days(self.slots)

    @rx.var
    def selected_date_slots(self) -> list[BookingSlotRow]:
        if self.selected_date == "__none__":
            return []
        return [item for item in self.slots if item["date"] == self.selected_date]

    @rx.var
    def has_selected_date_slots(self) -> bool:
        return bool(self.selected_date_slots)

    @rx.var
    def has_doctors(self) -> bool:
        return bool(self.doctors)

    @rx.var
    def has_slots(self) -> bool:
        return bool(self.slots)

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear_feedback(self) -> None:
        self.error_message = ""
        self.success_message = ""

    def _reset_selection(self) -> None:
        self.selected_specialty = "__none__"
        self.selected_doctor = "__none__"
        self.selected_date = "__none__"
        self.selected_slot_id = 0
        self.selected_slot_label = ""
        self.selected_doctor_name = ""
        self.confirmation_open = False
        self.doctors = []
        self.slots = []

    async def _redirect_for_auth(self, exc: Exception):
        self.specialties = []
        self._reset_selection()
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
            with rx.session() as db:
                specialties, doctors, slots = patient_get_booking_options(
                    db, token=token
                )
            self.specialties = [
                {"value": str(item.id), "label": item.name}
                for item in specialties
            ]
            self._reset_selection()
            self.booked = False
            self.booked_description = ""
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._redirect_for_auth(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível carregar a disponibilidade agora. Tente novamente."
            )
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def choose_specialty(self, value: str):
        self.selected_specialty = value
        self.selected_doctor = "__none__"
        self.selected_date = "__none__"
        self.doctors = []
        self.slots = []
        self.selected_slot_id = 0
        self.confirmation_open = False
        self._clear_feedback()
        if value == "__none__":
            return
        self.is_loading = True
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                _, doctors, _ = patient_get_booking_options(
                    db, token=token, specialty_id=int(value)
                )
            self.doctors = [
                {"value": str(item.id),
                 "label": item.name}
                for item in doctors
            ]
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._redirect_for_auth(exc):
                yield event
        except (ValueError, SchedulingValidationError):
            self.error_message = "Especialidade inválida. Selecione uma opção válida."
        except Exception:
            self.error_message = "Não foi possível consultar os médicos disponíveis."
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def choose_doctor(self, value: str):
        self.selected_doctor = value
        self.selected_date = "__none__"
        self.slots = []
        self.selected_slot_id = 0
        self.confirmation_open = False
        self._clear_feedback()
        if self.selected_specialty == "__none__" or value == "__none__":
            return
        self.is_loading = True
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                _, _, slots = patient_get_booking_options(
                    db, token=token, specialty_id=int(self.selected_specialty),
                    professional_id=int(value),
                )
            self.slots = [
                {
                    "id": slot.id,
                    "date": format_clinic_datetime(slot.starts_at).split(" às ")[0],
                    "hour": format_clinic_datetime(slot.starts_at).split(" às ")[1],
                    "label": format_clinic_datetime(slot.starts_at),
                }
                for slot in slots
            ]
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._redirect_for_auth(exc):
                yield event
        except (ValueError, SchedulingValidationError):
            self.error_message = "Médico inválido. Selecione uma opção válida."
        except Exception:
            self.error_message = "Não foi possível consultar os horários."
        finally:
            self.is_loading = False
            yield

    @rx.event
    def choose_date(self, value: str) -> None:
        """Require an explicit available day before displaying its hours."""
        self._clear_feedback()
        self.selected_date = (
            value if any(item["date"] == value for item in self.slots) else "__none__"
        )
        self.selected_slot_id = 0
        self.selected_slot_label = ""
        self.confirmation_open = False

    @rx.event
    def review_slot(self, slot_id: int) -> None:
        self._clear_feedback()
        slot = next((s for s in self.slots if s["id"] == slot_id), None)
        doctor = next(
            (d for d in self.doctors if d["value"] == self.selected_doctor), None
        )
        if (slot is None or doctor is None or self.selected_date == "__none__"
                or slot["date"] != self.selected_date):
            self.error_message = "Selecione primeiro o dia e um horário livre dessa data."
            return
        self.selected_slot_id = slot_id
        self.selected_slot_label = slot["label"]
        self.selected_doctor_name = doctor["label"]
        self.confirmation_open = True

    @rx.event
    def set_confirmation_open(self, is_open: bool) -> None:
        if not self.is_submitting:
            self.confirmation_open = is_open

    @rx.event
    def cancel_confirmation(self) -> None:
        if not self.is_submitting:
            self.confirmation_open = False

    @rx.event
    async def confirm_booking(self):
        if self.is_submitting:
            return
        self._clear_feedback()
        if (
            self.selected_specialty == "__none__"
            or self.selected_doctor == "__none__"
            or not self.selected_slot_id
        ):
            self.error_message = "Escolha especialidade, médico e horário para continuar."
            yield
            return
        self.is_submitting = True
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                patient_schedule_own_consultation(
                    db, token=token,
                    specialty_id=int(self.selected_specialty),
                    professional_id=int(self.selected_doctor),
                    slot_id=self.selected_slot_id,
                )
            self.booked_description = (
                f"{self.selected_doctor_name} · {self.selected_slot_label}"
            )
            self.booked = True
            self.confirmation_open = False
            self.success_message = "Consulta agendada com sucesso."
            self.slots = []
            self.selected_date = "__none__"
        except (
            SchedulingConflictError, SchedulingNotFoundError,
            SchedulingValidationError, ValueError,
        ) as exc:
            self.error_message = str(exc)
            self.confirmation_open = False
            try:
                with rx.session() as db:
                    _, _, slots = patient_get_booking_options(
                        db, token=token,
                        specialty_id=int(self.selected_specialty),
                        professional_id=int(self.selected_doctor),
                    )
                self.slots = [
                    {
                        "id": slot.id,
                        "date": format_clinic_datetime(slot.starts_at).split(" às ")[0],
                        "hour": format_clinic_datetime(slot.starts_at).split(" às ")[1],
                        "label": format_clinic_datetime(slot.starts_at),
                    }
                    for slot in slots
                ]
            except Exception:
                self.slots = []
            if not any(slot["date"] == self.selected_date for slot in self.slots):
                self.selected_date = "__none__"
            self.selected_slot_id = 0
            self.selected_slot_label = ""
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._redirect_for_auth(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível concluir o agendamento. Atualize a lista e tente novamente."
            )
            self.confirmation_open = False
        finally:
            self.is_submitting = False
            yield
