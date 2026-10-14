"""Reflex state for a securely loaded reception dashboard."""
from datetime import datetime

import reflex as rx
from vitta_one.appointment_scheduling.temporal import format_clinic_datetime
from vitta_one.auth.authorization import (
    AuthenticationRequiredError, PasswordChangeRequiredError, RoleForbiddenError,
)
from vitta_one.auth.state import AuthState
from vitta_one.reception.dashboard.application import reception_overview


class ReceptionDashboardState(rx.State):
    scheduled_today: int = 0
    waiting: int = 0
    attending: int = 0
    finished_today: int = 0
    confirmed_today: int = 0
    arrivals_pending: int = 0
    waiting_red: int = 0
    waiting_yellow: int = 0
    waiting_green: int = 0
    next_consultations: list[dict[str, str]] = []
    clinic_day: str = ""
    last_updated: str = ""
    is_loading: bool = False
    error_message: str = ""

    def _clear_data(self) -> None:
        self.scheduled_today = 0
        self.waiting = 0
        self.attending = 0
        self.finished_today = 0
        self.confirmed_today = 0
        self.arrivals_pending = 0
        self.waiting_red = 0
        self.waiting_yellow = 0
        self.waiting_green = 0
        self.next_consultations = []
        self.clinic_day = ""
        self.last_updated = ""

    @rx.event
    async def load(self):
        """Every refresh revalidates the session and role before reading data."""
        self.is_loading = True
        self.error_message = ""
        yield
        try:
            auth = await self.get_state(AuthState)
            with rx.session() as db:
                snapshot = reception_overview(db, token=auth.session_token)
            self.scheduled_today = snapshot.scheduled_today
            self.waiting = snapshot.waiting
            self.attending = snapshot.attending
            self.finished_today = snapshot.finished_today
            self.confirmed_today = snapshot.confirmed_today
            self.arrivals_pending = snapshot.arrivals_pending
            self.waiting_red = snapshot.waiting_red
            self.waiting_yellow = snapshot.waiting_yellow
            self.waiting_green = snapshot.waiting_green
            self.next_consultations = [
                {
                    "id": str(item.id),
                    "patient": item.patient_name,
                    "professional": item.professional_name,
                    "when": format_clinic_datetime(item.scheduled_at),
                }
                for item in snapshot.next_consultations
            ]
            day = datetime.fromisoformat(snapshot.clinic_date)
            self.clinic_day = day.strftime("%d/%m/%Y")
            self.last_updated = format_clinic_datetime(snapshot.as_of)
        except (AuthenticationRequiredError, PasswordChangeRequiredError):
            self._clear_data()
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self._clear_data()
            yield rx.redirect("/acesso-negado")
        except Exception:
            self._clear_data()
            self.error_message = "Não foi possível atualizar o painel agora. Tente novamente."
        finally:
            self.is_loading = False
            yield
