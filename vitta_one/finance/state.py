"""Reflex state for the Financeiro operational workspace."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, TypedDict

import reflex as rx
from sqlmodel import select

from vitta_one.auth.authorization import AuthenticationRequiredError, PasswordChangeRequiredError, RoleForbiddenError, require_role
from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState
from vitta_one.finance.application import (
    finance_cancel_charge, finance_create_charge, finance_create_service,
    finance_dashboard, finance_issue_account, finance_list_accounts,
    finance_list_services, finance_reconcile_charge, finance_set_service_active,
)
from vitta_one.finance.service import AccountItemInput, FinanceError
from vitta_one.integrations.asaas import AsaasUnavailableError
from vitta_one.integrations.settings import integration_status
from vitta_one.models.patient_queue import Patient


class FinanceAccountRow(TypedDict):
    id: int
    patient_name: str
    due_date: str
    total: str
    paid: str
    balance: str
    status: str
    charge_id: int
    charge_status: str
    invoice_url: str


class FinanceServiceRow(TypedDict):
    id: int
    name: str
    price: str
    active: bool


class FinancePatientRow(TypedDict):
    id: int
    name: str


def _money(cents: int) -> str:
    return f"R$ {cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _parse_money(value: str) -> int:
    raw = str(value or "").strip().replace("R$", "").replace(" ", "")
    if not raw:
        raise FinanceError("Informe o valor do serviço.")
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        amount = Decimal(raw).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise FinanceError("Informe um valor monetário válido.") from exc
    cents = int(amount * 100)
    if cents <= 0:
        raise FinanceError("O valor deve ser positivo.")
    return cents


class FinanceState(rx.State):
    account_rows: list[FinanceAccountRow] = []
    service_rows: list[FinanceServiceRow] = []
    patient_rows: list[FinancePatientRow] = []
    open_total: str = "R$ 0,00"
    overdue_total: str = "R$ 0,00"
    received_total: str = "R$ 0,00"
    account_count: int = 0
    asaas_status: str = "NOT_CONFIGURED"
    is_loading: bool = False
    is_submitting: bool = False
    error_message: str = ""
    success_message: str = ""
    account_query: str = ""
    account_status_filter: str = "TODOS"
    cancel_charge_dialog_open: bool = False
    cancel_charge_id: int = 0
    cancel_charge_patient_name: str = ""

    @rx.var
    def has_accounts(self) -> bool:
        return bool(self.account_rows)

    @rx.var
    def has_services(self) -> bool:
        return any(row["active"] for row in self.service_rows)

    @rx.var
    def filtered_account_rows(self) -> list[FinanceAccountRow]:
        term = self.account_query.strip().casefold()
        return [
            row for row in self.account_rows
            if (not term or term in row["patient_name"].casefold())
            and (
                self.account_status_filter == "TODOS"
                or row["status"] == self.account_status_filter
                or row["charge_status"] == self.account_status_filter
            )
        ]

    async def _token(self) -> str:
        return (await self.get_state(AuthState)).session_token

    def _clear(self) -> None:
        self.account_rows = []
        self.service_rows = []
        self.patient_rows = []
        self.open_total = self.overdue_total = self.received_total = "R$ 0,00"
        self.account_count = 0
        self.cancel_charge_dialog_open = False
        self.cancel_charge_id = 0
        self.cancel_charge_patient_name = ""

    @rx.event
    async def load(self):
        self.is_loading = True
        self.error_message = ""
        self.success_message = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                identity = require_role(db, token, Role.FINANCEIRO)
                summary = finance_dashboard(db, token=token)
                accounts = finance_list_accounts(db, token=token)
                services = finance_list_services(db, token=token, include_inactive=True)
                patients = db.exec(select(Patient).order_by(Patient.name, Patient.id)).all()
            self.open_total = _money(summary.open_cents)
            self.overdue_total = _money(summary.overdue_cents)
            self.received_total = _money(summary.received_cents)
            self.account_count = summary.account_count
            self.account_rows = [
                {
                    "id": item.id, "patient_name": item.patient_name,
                    "due_date": item.due_date.strftime("%d/%m/%Y"),
                    "total": _money(item.total_cents), "paid": _money(item.paid_cents),
                    "balance": _money(item.balance_cents), "status": item.status,
                    "charge_id": item.charge_id, "charge_status": item.charge_status,
                    "invoice_url": item.invoice_url,
                }
                for item in accounts
            ]
            self.service_rows = [
                {
                    "id": item.id,
                    "name": item.name,
                    "price": _money(item.unit_price_cents),
                    "active": item.active,
                }
                for item in services
            ]
            self.patient_rows = [{"id": item.id, "name": item.name} for item in patients if item.id is not None]
            self.asaas_status = integration_status()["asaas"]
        except (AuthenticationRequiredError, RoleForbiddenError, PasswordChangeRequiredError) as exc:
            self._clear()
            yield rx.redirect("/login" if isinstance(exc, AuthenticationRequiredError) else "/acesso-negado")
        except Exception:
            self._clear()
            self.error_message = "Não foi possível carregar o financeiro agora. Tente novamente."
        finally:
            self.is_loading = False
            yield

    @rx.event
    def update_account_query(self, value: str) -> None:
        self.account_query = str(value or "")[:100]

    @rx.event
    def update_account_status_filter(self, value: str) -> None:
        allowed = {"TODOS", "OPEN", "PARTIALLY_PAID", "PAID", "PENDING", "OVERDUE", "RECONCILIATION_REQUIRED"}
        self.account_status_filter = value if value in allowed else "TODOS"

    @rx.event
    def begin_cancel_charge(self, charge_id: int, patient_name: str) -> None:
        if self.is_submitting or charge_id <= 0:
            return
        self.cancel_charge_id = charge_id
        self.cancel_charge_patient_name = patient_name[:160]
        self.cancel_charge_dialog_open = True

    @rx.event
    def set_cancel_charge_dialog_open(self, is_open: bool) -> None:
        if self.is_submitting and not is_open:
            return
        self.cancel_charge_dialog_open = is_open
        if not is_open:
            self.cancel_charge_id = 0
            self.cancel_charge_patient_name = ""

    @rx.event
    async def create_service(self, form_data: dict[str, Any]):
        if self.is_submitting:
            return
        self.is_submitting = True
        self.error_message = self.success_message = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                finance_create_service(
                    db, token=token, name=form_data.get("name", ""),
                    description=form_data.get("description", ""),
                    unit_price_cents=_parse_money(form_data.get("price", "")),
                )
            async for event in self.load():
                yield event
            self.success_message = "Serviço cadastrado com sucesso."
        except FinanceError as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError, PasswordChangeRequiredError) as exc:
            yield rx.redirect("/login" if isinstance(exc, AuthenticationRequiredError) else "/acesso-negado")
        except Exception:
            self.error_message = "Não foi possível cadastrar o serviço. Tente novamente."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def set_service_active(self, service_id: int, active: bool):
        if self.is_submitting:
            return
        self.is_submitting = True
        self.error_message = self.success_message = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                finance_set_service_active(
                    db,
                    token=token,
                    service_id=service_id,
                    active=active,
                )
            async for event in self.load():
                yield event
            self.success_message = "Serviço ativado." if active else "Serviço desativado."
        except FinanceError as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError, PasswordChangeRequiredError) as exc:
            yield rx.redirect("/login" if isinstance(exc, AuthenticationRequiredError) else "/acesso-negado")
        except Exception:
            self.error_message = "Não foi possível atualizar o serviço."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def issue_account(self, form_data: dict[str, Any]):
        if self.is_submitting:
            return
        self.is_submitting = True
        self.error_message = self.success_message = ""
        yield
        try:
            patient_id = int(form_data.get("patient_id", "0"))
            service_id = int(form_data.get("service_id", "0"))
            quantity = int(form_data.get("quantity", "1"))
            due_date = date.fromisoformat(form_data.get("due_date", ""))
            token = await self._token()
            with rx.session() as db:
                finance_issue_account(
                    db, token=token, patient_id=patient_id, due_date=due_date,
                    items=[AccountItemInput(service_id, quantity)],
                )
            async for event in self.load():
                yield event
            self.success_message = "Conta emitida com sucesso."
        except (ValueError, FinanceError) as exc:
            self.error_message = str(exc) if isinstance(exc, FinanceError) else "Preencha paciente, serviço, quantidade e vencimento."
        except (AuthenticationRequiredError, RoleForbiddenError, PasswordChangeRequiredError) as exc:
            yield rx.redirect("/login" if isinstance(exc, AuthenticationRequiredError) else "/acesso-negado")
        except Exception:
            self.error_message = "Não foi possível emitir a conta. Tente novamente."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def create_charge(self, account_id: int, billing_type: str):
        if self.is_submitting:
            return
        self.is_submitting = True
        self.error_message = self.success_message = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                finance_create_charge(db, token=token, account_id=account_id, billing_type=billing_type)
            async for event in self.load():
                yield event
            self.success_message = "Cobrança enviada ao Asaas Sandbox."
        except (FinanceError, AsaasUnavailableError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError, PasswordChangeRequiredError) as exc:
            yield rx.redirect("/login" if isinstance(exc, AuthenticationRequiredError) else "/acesso-negado")
        except Exception:
            self.error_message = "Não foi possível emitir a cobrança. Tente novamente."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def cancel_charge(self):
        if self.is_submitting or self.cancel_charge_id <= 0:
            return
        self.is_submitting = True
        self.error_message = self.success_message = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                finance_cancel_charge(db, token=token, charge_id=self.cancel_charge_id)
            async for event in self.load():
                yield event
            self.cancel_charge_dialog_open = False
            self.cancel_charge_id = 0
            self.cancel_charge_patient_name = ""
            self.success_message = "Cobrança cancelada."
        except (FinanceError, AsaasUnavailableError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError, PasswordChangeRequiredError) as exc:
            yield rx.redirect("/login" if isinstance(exc, AuthenticationRequiredError) else "/acesso-negado")
        except Exception:
            self.error_message = "Não foi possível cancelar a cobrança."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def reconcile_charge(self, charge_id: int):
        if self.is_submitting or charge_id <= 0:
            return
        self.is_submitting = True
        self.error_message = self.success_message = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                finance_reconcile_charge(db, token=token, charge_id=charge_id)
            async for event in self.load():
                yield event
            self.success_message = "Cobrança reconciliada com o Asaas."
        except (FinanceError, AsaasUnavailableError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError, PasswordChangeRequiredError) as exc:
            yield rx.redirect("/login" if isinstance(exc, AuthenticationRequiredError) else "/acesso-negado")
        except Exception:
            self.error_message = "Não foi possível verificar a cobrança agora."
        finally:
            self.is_submitting = False
            yield

