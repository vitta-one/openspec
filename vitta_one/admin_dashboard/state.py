"""Reflex state for the protected administrative dashboard projection."""
import reflex as rx

from vitta_one.auth.authorization import (
    AuthenticationRequiredError,
    PasswordChangeRequiredError,
    RoleForbiddenError,
)
from vitta_one.auth.state import AuthState
from vitta_one.admin_dashboard.application import admin_dashboard_snapshot


class AdminDashboardState(rx.State):
    active_professionals: int = 0
    active_specialties: int = 0
    consultations_today: int = 0
    staff_accounts: int = 0
    clinic_date: str = ""
    is_loading: bool = True
    has_loaded: bool = False
    error_message: str = ""

    def _clear(self) -> None:
        self.active_professionals = 0
        self.active_specialties = 0
        self.consultations_today = 0
        self.staff_accounts = 0
        self.clinic_date = ""
        self.has_loaded = False

    async def _token(self) -> str:
        return (await self.get_state(AuthState)).session_token

    @rx.event
    async def load(self):
        self.is_loading = True
        self.error_message = ""
        yield
        try:
            with rx.session() as db:
                snapshot = admin_dashboard_snapshot(db, token=await self._token())
            self.active_professionals = snapshot.active_professionals
            self.active_specialties = snapshot.active_specialties
            self.consultations_today = snapshot.consultations_today
            self.staff_accounts = snapshot.staff_accounts
            self.clinic_date = snapshot.clinic_date
            self.has_loaded = True
        except (AuthenticationRequiredError, PasswordChangeRequiredError):
            self._clear()
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self._clear()
            yield rx.redirect("/acesso-negado")
        except Exception:
            self._clear()
            self.error_message = "Não foi possível carregar os indicadores administrativos. Tente novamente."
        finally:
            self.is_loading = False
            yield
