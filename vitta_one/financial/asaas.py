"""Backend-only Asaas v3 Sandbox adapter. No automatic mutation retries."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from decimal import Decimal, InvalidOperation
import json
import os
import re
from typing import Any
from urllib.parse import urlsplit

import httpx


SANDBOX = "https://api-sandbox.asaas.com/v3"
TIMEOUT = httpx.Timeout(connect=3, read=10, write=10, pool=3)


class FinancialError(ValueError):
    """Safe operational error, without provider payloads or credentials."""


class ConfigurationError(FinancialError):
    pass


class ProviderRejected(FinancialError):
    def __init__(self, status_code: int):
        super().__init__(f"Operação recusada pelo Asaas (HTTP {status_code}).")
        self.status_code = status_code


class ProviderUnknown(FinancialError):
    def __init__(self, retry_after: int = 0):
        super().__init__("Resultado externo desconhecido. Concilie antes de repetir a operação.")
        self.retry_after = retry_after


def amount(value: object) -> Decimal:
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result <= 0 or result > Decimal("9999999999.99"):
            raise ValueError
        if result != result.quantize(Decimal("0.01")):
            raise ValueError
        return result.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        raise FinancialError("Informe um valor positivo em reais com até duas casas decimais.") from None


def payment_url(value: object) -> str:
    if not value:
        return ""
    try:
        parsed = urlsplit(str(value))
        port = parsed.port
    except ValueError:
        raise FinancialError("Link de pagamento inválido.") from None
    if (parsed.scheme != "https" or parsed.username or parsed.password or port not in (None, 443)
            or parsed.hostname not in {"sandbox.asaas.com", "www.asaas.com", "asaas.com"}):
        raise FinancialError("Link de pagamento inválido.")
    return str(value)


def resource_id(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", value):
        raise FinancialError("Identificador externo inválido.")
    return value


@dataclass(frozen=True)
class AsaasClient:
    key: str = field(repr=False)
    base_url: str = SANDBOX
    transport: httpx.BaseTransport | None = field(default=None, repr=False)

    def __post_init__(self):
        if not self.key.strip() or self.key.startswith("$aact_prod_") or self.base_url != SANDBOX:
            raise ConfigurationError("Configure a chave e a URL oficiais do Asaas Sandbox no servidor.")

    @classmethod
    def from_env(cls) -> "AsaasClient":
        return cls(os.getenv("ASAAS_API_KEY", "").strip(), os.getenv("ASAAS_BASE_URL", SANDBOX).rstrip("/"))

    def request(self, method: str, path: str, *, payload: dict | None = None, params: dict | None = None) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=TIMEOUT, transport=self.transport, follow_redirects=False) as client:
                response = client.request(
                    method, self.base_url + path,
                    headers={"access_token": self.key, "User-Agent": "Vitta-One/1.0", "Content-Type": "application/json"},
                    content=json.dumps(payload).encode() if payload is not None else None, params=params,
                )
        except httpx.HTTPError:
            raise ProviderUnknown() from None
        if response.status_code >= 500 or response.status_code == 429 or 300 <= response.status_code < 400:
            retry = response.headers.get("Retry-After", "0")
            try:
                seconds = int(retry)
            except ValueError:
                try:
                    seconds = int((parsedate_to_datetime(retry) - datetime.now(timezone.utc)).total_seconds())
                except (ValueError, TypeError, OverflowError):
                    seconds = 0
            raise ProviderUnknown(retry_after=max(0, min(seconds, 86400)))
        if not 200 <= response.status_code < 300:
            raise ProviderRejected(response.status_code)
        try:
            result = json.loads(response.content, parse_float=Decimal)
        except (ValueError, UnicodeError):
            raise ProviderUnknown() from None
        if not isinstance(result, dict):
            raise ProviderUnknown()
        return result

    def find(self, collection: str, reference: str, *, query_field="externalReference") -> list[dict]:
        if collection not in {"customers", "payments"}:
            raise FinancialError("Coleção inválida.")
        if query_field != "externalReference" and (collection != "customers" or query_field != "cpfCnpj"):
            raise FinancialError("Filtro externo inválido.")
        found: list[dict] = []
        offset = 0
        for _ in range(100):
            page = self.request("GET", f"/{collection}", params={query_field: reference, "offset": offset, "limit": 100})
            rows = page.get("data")
            if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                raise ProviderUnknown()
            # Never bind a provider record merely because a search returned it.
            found.extend(row for row in rows if row.get(query_field) == reference)
            if not page.get("hasMore"):
                return found
            if not rows:
                raise ProviderUnknown()
            offset += len(rows)
        raise ProviderUnknown()

    def create_customer(self, *, name: str, cpf: str, reference: str) -> dict:
        from vitta_one.patient_queue.service import is_valid_cpf
        if not 2 <= len(name.strip()) <= 160 or not is_valid_cpf(cpf):
            raise FinancialError("Cadastro do paciente inválido para cobrança.")
        return self.request("POST", "/customers", payload={"name": name.strip(), "cpfCnpj": cpf,
                            "externalReference": reference, "notificationDisabled": True})

    def update_customer(self, customer_id: str, *, name: str, cpf: str) -> dict:
        from vitta_one.patient_queue.service import is_valid_cpf
        if not 2 <= len(name.strip()) <= 160 or not is_valid_cpf(cpf):
            raise FinancialError("Cadastro do paciente inválido.")
        return self.request("PUT", f"/customers/{resource_id(customer_id)}", payload={"name": name.strip(), "cpfCnpj": cpf})

    def create_payment(self, *, customer_id: str, billing_type: str, value: Decimal, due_date: date, reference: str) -> dict:
        if billing_type not in {"PIX", "BOLETO"}:
            raise FinancialError("Método não homologado. Utilize Pix ou boleto.")
        validated = amount(value)
        # JSON number with exactly two decimal places, without binary money arithmetic.
        payload = {"customer": resource_id(customer_id), "billingType": billing_type,
                   "value": float(validated), "dueDate": due_date.isoformat(), "externalReference": reference}
        return self.request("POST", "/payments", payload=payload)

    def payment(self, payment_id: str) -> dict:
        return self.request("GET", f"/payments/{resource_id(payment_id)}")

    def pix(self, payment_id: str) -> dict:
        return self.request("GET", f"/payments/{resource_id(payment_id)}/pixQrCode")

    def cancel(self, payment_id: str) -> dict:
        return self.request("DELETE", f"/payments/{resource_id(payment_id)}")

    def refund(self, payment_id: str) -> dict:
        return self.request("POST", f"/payments/{resource_id(payment_id)}/refund", payload={})
