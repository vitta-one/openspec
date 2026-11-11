"""Reflex event boundary; each operation revalidates the server session."""
from datetime import date, timedelta
from typing import Any
import reflex as rx

from vitta_one.auth.state import AuthState
from . import application as app, service
from .asaas import FinancialError


class FinancialState(rx.State):
    rows: list[dict[str, str]] = []
    evolution: list[dict[str, str]] = []
    candidates: list[str] = []
    history: list[dict[str, str]] = []
    query: str = ""
    status_filter: str = ""
    start: str = ""
    end: str = ""
    page: int = 1
    total: int = 0
    received: str = "R$ 0,00"
    pending: str = "R$ 0,00"
    overdue: str = "R$ 0,00"
    confirmed: str = "R$ 0,00"
    error: str = ""
    success: str = ""
    busy: bool = False
    detail_open: bool = False
    selected_id: int = 0
    selected_name: str = ""
    selected_info: str = ""
    selected_url: str = ""
    pix_payload: str = ""
    operation: str = ""
    confirmation_open: bool = False

    def _clear(self):
        self.rows, self.evolution, self.candidates, self.history = [], [], [], []
        self.selected_id = 0
        self.selected_name = self.selected_info = self.selected_url = self.pix_payload = ""
        self.detail_open = self.confirmation_open = False
        self.total = 0
        self.received = self.pending = self.overdue = self.confirmed = "R$ 0,00"
        self.query = ""

    async def _token(self):
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _refresh(self, token):
        if not self.end:
            self.end = service.now().astimezone(service.clinic_timezone()).date().isoformat()
            self.start = (date.fromisoformat(self.end) - timedelta(days=29)).isoformat()
        with rx.session() as db:
            data = app.snapshot(db, token=token, search=self.query, status=self.status_filter,
                                start=date.fromisoformat(self.start), end=date.fromisoformat(self.end), page=self.page)
        self.rows, self.evolution, self.candidates = data["rows"], data["evolution"], data["candidates"]
        self.page, self.total = data["page"], data["total"]
        self.received, self.pending = data["totals"]["RECEIVED"], data["totals"]["PENDING"]
        self.overdue, self.confirmed = data["totals"]["OVERDUE"], data["totals"]["CONFIRMED"]

    async def _failure(self, exc):
        self._clear()
        if isinstance(exc, PermissionError):
            self.error = "Sua sessão não permite esta operação. Entre novamente ou verifique o perfil."
        elif isinstance(exc, (ValueError, FinancialError)):
            self.error = str(exc)
        else:
            self.error = "Não foi possível consultar o financeiro. Tente atualizar novamente."

    @rx.event
    async def load(self):
        if self.busy:
            return
        self.busy, self.error = True, ""
        yield
        try:
            self._refresh(await self._token())
        except Exception as exc:
            await self._failure(exc)
        finally:
            self.busy = False

    @rx.event
    async def filter(self, data: dict[str, Any]):
        self.query, self.status_filter = data.get("query", ""), data.get("status", "")
        if self.status_filter == "ALL":
            self.status_filter = ""
        self.start, self.end, self.page = data.get("start", ""), data.get("end", ""), 1
        async for _ in self.load():
            yield

    @rx.event
    async def change_page(self, delta: int):
        self.page = max(1, self.page + delta)
        async for _ in self.load():
            yield

    @rx.event
    async def issue(self, data: dict[str, Any]):
        if self.busy:
            return
        self.busy, self.error, self.success = True, "", ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                charge = service.create_charge(db, token=token, consultation_id=int(data.get("consultation", "").split(" · ")[0]),
                            value=data.get("value", "").replace(",", "."), due_date=date.fromisoformat(data.get("due", "")), method=data.get("method", ""))
                identifier = charge.id
            self._refresh(token)
            self.success = "Cobrança registrada no Asaas Sandbox."
            self._show(token, identifier)
        except Exception as exc:
            await self._failure(exc)
        finally:
            self.busy = False

    def _show(self, token, charge_id):
        with rx.session() as db:
            detail = app.charge_detail(db, token=token, charge_id=charge_id)
        self.selected_id, self.selected_name = charge_id, detail["patient"]
        self.selected_info = f"Consulta {detail['consultation']} · {detail['value']} · {detail['method']} · {detail['due']} · {detail['status']} · {detail['external_id']}"
        self.selected_url, self.history, self.pix_payload = detail["url"], detail["history"], ""
        self.detail_open = True

    @rx.event
    async def show(self, charge_id: str):
        try:
            self.error = ""
            self._show(await self._token(), int(charge_id))
        except Exception as exc:
            await self._failure(exc)

    @rx.event
    async def reconcile_selected(self):
        if self.busy or not self.selected_id:
            return
        self.busy, self.error = True, ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                service.reconcile(db, token=token, charge_id=self.selected_id)
            self._refresh(token)
            self._show(token, self.selected_id)
        except Exception as exc:
            await self._failure(exc)
        finally:
            self.busy = False

    @rx.event
    async def get_pix(self):
        try:
            with rx.session() as db:
                data = service.pix_data(db, token=await self._token(), charge_id=self.selected_id)
            payload = data.get("payload")
            if not isinstance(payload, str) or len(payload) > 4096:
                raise FinancialError("Dados Pix indisponíveis.")
            self.pix_payload = payload
        except Exception as exc:
            if isinstance(exc, PermissionError):
                await self._failure(exc)
            else:
                self.error = str(exc) if isinstance(exc, ValueError) else "Não foi possível consultar o Pix."

    @rx.event
    async def sync_customer(self):
        try:
            token = await self._token()
            with rx.session() as db:
                service.authorize(db, token)
                charge = db.get(service.FinancialCharge, self.selected_id)
                if charge is None:
                    raise FinancialError("Cobrança não encontrada.")
                customer = db.get(service.FinancialCustomer, charge.customer_id)
                service.sync_customer(db, token=token, patient_id=customer.patient_id)
            self.success = "Cadastro financeiro atualizado com os dados atuais do paciente."
        except Exception as exc:
            if isinstance(exc, PermissionError):
                await self._failure(exc)
            else:
                self.error = str(exc) if isinstance(exc, ValueError) else "Não foi possível atualizar o cliente. Concilie antes de repetir."

    @rx.event
    def request_operation(self, operation: str):
        if operation in {"CANCEL", "REFUND"}:
            self.operation, self.confirmation_open = operation, True

    @rx.event
    async def confirm_operation(self, data: dict[str, Any]):
        if self.busy:
            return
        self.busy, self.error, self.success = True, "", ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                service.mutate_charge(db, token=token, charge_id=self.selected_id, operation=self.operation, reason=data.get("reason", ""))
            self.confirmation_open = False
            self._refresh(token)
            self._show(token, self.selected_id)
            self.success = "Operação registrada e situação conciliada."
        except Exception as exc:
            if isinstance(exc, PermissionError):
                await self._failure(exc)
            else:
                self.error = str(exc) if isinstance(exc, ValueError) else "Não foi possível confirmar a operação. Concilie antes de repetir."
        finally:
            self.busy = False

    @rx.event
    def close_detail(self, value: bool):
        self.detail_open = value

    @rx.event
    def close_confirmation(self, value: bool):
        if not self.busy:
            self.confirmation_open = value
