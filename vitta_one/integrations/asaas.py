"""Asaas billing client, Sandbox by default."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from time import sleep
from typing import Any

import httpx

from .settings import AsaasSettings


class AsaasError(RuntimeError):
    pass


class AsaasUnavailableError(AsaasError):
    pass


@dataclass(frozen=True)
class AsaasCustomer:
    id: str


@dataclass(frozen=True)
class AsaasCharge:
    id: str
    status: str
    invoice_url: str | None


def cents_to_decimal(cents: int) -> str:
    return f"{Decimal(cents) / Decimal(100):.2f}"


class AsaasClient:
    def __init__(self, settings: AsaasSettings, *, transport: httpx.BaseTransport | None = None) -> None:
        self.settings = settings
        self._client = httpx.Client(
            base_url=settings.base_url,
            headers={"access_token": settings.api_key, "User-Agent": settings.user_agent, "Content-Type": "application/json"},
            timeout=settings.timeout_seconds,
            transport=transport,
            follow_redirects=False,
        )

    @staticmethod
    def _json(response: httpx.Response) -> dict[str, Any]:
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid payload")
        return payload

    def _get_json(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self._client.get(path, params=params)
                if response.status_code == 429 or response.status_code >= 500:
                    raise httpx.HTTPStatusError("retryable response", request=response.request, response=response)
                return self._json(response)
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt < 2:
                    sleep(0.05 * (2**attempt))
        raise AsaasUnavailableError("O serviço financeiro está temporariamente indisponível.") from last_error

    def find_customer(self, external_reference: str) -> AsaasCustomer | None:
        try:
            payload = self._get_json("/customers", params={"externalReference": external_reference, "limit": 1})
            items = payload.get("data") or []
            return AsaasCustomer(str(items[0]["id"])) if items else None
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise AsaasUnavailableError("Não foi possível consultar o cadastro financeiro.") from exc

    def create_customer(self, *, name: str, cpf_cnpj: str, external_reference: str) -> AsaasCustomer:
        try:
            payload = self._json(self._client.post("/customers", json={
                "name": name,
                "cpfCnpj": cpf_cnpj,
                "externalReference": external_reference,
            }))
            return AsaasCustomer(str(payload["id"]))
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise AsaasUnavailableError("Não foi possível criar o cadastro financeiro.") from exc

    def find_charge(self, external_reference: str) -> AsaasCharge | None:
        try:
            payload = self._get_json("/payments", params={"externalReference": external_reference, "limit": 1})
            items = payload.get("data") or []
            return self._charge(items[0]) if items else None
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise AsaasUnavailableError("Não foi possível reconciliar a cobrança.") from exc

    @staticmethod
    def _charge(payload: dict[str, Any]) -> AsaasCharge:
        return AsaasCharge(
            id=str(payload["id"]), status=str(payload.get("status") or "PENDING"),
            invoice_url=str(payload["invoiceUrl"]) if payload.get("invoiceUrl") else None,
        )

    def create_charge(self, *, customer_id: str, billing_type: str, value_cents: int, due_date: date, description: str, external_reference: str) -> AsaasCharge:
        body = {
            "customer": customer_id,
            "billingType": billing_type,
            "value": cents_to_decimal(value_cents),
            "dueDate": due_date.isoformat(),
            "description": description[:500],
            "externalReference": external_reference,
        }
        try:
            return self._charge(self._json(self._client.post("/payments", json=body)))
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise AsaasUnavailableError("Não foi possível emitir a cobrança.") from exc

    def cancel_charge(self, charge_id: str) -> None:
        try:
            self._json(self._client.delete(f"/payments/{charge_id}"))
        except (httpx.HTTPError, TypeError, ValueError) as exc:
            raise AsaasUnavailableError("Não foi possível cancelar a cobrança.") from exc
