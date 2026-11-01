"""Scoped State for /admin/recepcao; never exposes reception write handlers."""

from datetime import date

import reflex as rx

from vitta_one.admin_preview.reception_service import load_reception_preview
from vitta_one.admin_preview.service import LocalAdminPreviewDisabledError
from vitta_one.appointment_scheduling.temporal import clinic_date_after_iso
from vitta_one.auth.authorization import (
    AuthenticationRequiredError,
    PasswordChangeRequiredError,
    RoleForbiddenError,
)
from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState


class AdminReceptionPreviewState(rx.State):
    """Minimal server-authorized operational data for local Administrator QA."""

    active_rows: list[dict[str, str]] = []
    history_rows: list[dict[str, str]] = []
    consultation_rows: list[dict[str, str]] = []
    professional_options: list[dict[str, str]] = []

    waiting_count: int = 0
    attending_count: int = 0
    finalized_count: int = 0
    withdrawn_count: int = 0
    history_total: int = 0
    consultation_total: int = 0

    start_date: str = ""
    end_date: str = ""
    priority_filter: str = "__all__"
    status_filter: str = "__all__"
    professional_filter: str = "__all__"

    updated_at: str = ""
    error_message: str = ""
    is_loading: bool = False

    def _clear_data(self) -> None:
        self.active_rows = []
        self.history_rows = []
        self.consultation_rows = []
        self.professional_options = []
        self.waiting_count = 0
        self.attending_count = 0
        self.finalized_count = 0
        self.withdrawn_count = 0
        self.history_total = 0
        self.consultation_total = 0
        self.updated_at = ""

    @rx.var
    def period_label(self) -> str:
        try:
            start = date.fromisoformat(self.start_date).strftime("%d/%m/%Y")
            end = date.fromisoformat(self.end_date).strftime("%d/%m/%Y")
        except ValueError:
            return "Período não selecionado"
        return f"{start} a {end}"

    @rx.event
    def update_start_date(self, value: str) -> None:
        self.start_date = str(value or "")[:10]

    @rx.event
    def update_end_date(self, value: str) -> None:
        self.end_date = str(value or "")[:10]

    @rx.event
    def update_priority_filter(self, value: str) -> None:
        self.priority_filter = str(value or "__all__")

    @rx.event
    def update_status_filter(self, value: str) -> None:
        self.status_filter = str(value or "__all__")

    @rx.event
    def update_professional_filter(self, value: str) -> None:
        self.professional_filter = str(value or "__all__")

    async def _reload(self):
        if self.is_loading:
            return
        self.is_loading = True
        self.error_message = ""
        self._clear_data()
        yield

        try:
            auth = await self.get_state(AuthState)
            with rx.session() as db:
                snapshot = load_reception_preview(
                    db,
                    token=auth.session_token,
                    start_day=self.start_date,
                    end_day=self.end_date,
                    priority_filter=self.priority_filter,
                    status_filter=self.status_filter,
                    professional_filter=self.professional_filter,
                )
            self.active_rows = snapshot.active_rows
            self.history_rows = snapshot.history_rows
            self.consultation_rows = snapshot.consultation_rows
            self.professional_options = snapshot.professional_options
            self.waiting_count = snapshot.waiting_count
            self.attending_count = snapshot.attending_count
            self.finalized_count = snapshot.finalized_count
            self.withdrawn_count = snapshot.withdrawn_count
            self.history_total = snapshot.history_total
            self.consultation_total = snapshot.consultation_total
            self.updated_at = snapshot.updated_at
        except LocalAdminPreviewDisabledError:
            self._clear_data()
            yield rx.redirect(Role.ADMINISTRADOR.dashboard_path)
        except (AuthenticationRequiredError, PasswordChangeRequiredError):
            self._clear_data()
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self._clear_data()
            yield rx.redirect("/acesso-negado")
        except ValueError as exc:
            self._clear_data()
            self.error_message = str(exc)
        except Exception:
            self._clear_data()
            self.error_message = "Não foi possível carregar as informações. Tente novamente."
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def load(self):
        if not self.start_date or not self.end_date:
            self.start_date = clinic_date_after_iso(-7)
            self.end_date = clinic_date_after_iso(7)
        async for event in self._reload():
            yield event

    @rx.event
    async def apply_filters(self):
        async for event in self._reload():
            yield event

    @rx.event
    async def refresh(self):
        async for event in self._reload():
            yield event

    @rx.event
    async def tick(self, _value: str):
        """Reuse the same 60-second refresh cadence as the reception dashboard."""
        if not self.is_loading:
            async for event in self._reload():
                yield event
