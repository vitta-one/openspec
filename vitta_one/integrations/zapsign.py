"""ZapSign document client restricted to the prescription flow."""

from dataclasses import dataclass
from typing import Any
from time import sleep

import httpx

from .settings import ZapSignSettings


class ZapSignError(RuntimeError):
    pass


class ZapSignUnavailableError(ZapSignError):
    pass


@dataclass(frozen=True)
class ZapSignDocument:
    token: str
    status: str
    signer_token: str | None
    signed_file: str | None = None


class ZapSignClient:
    def __init__(self, settings: ZapSignSettings, *, transport: httpx.BaseTransport | None = None) -> None:
        self.settings = settings
        self._client = httpx.Client(
            base_url=settings.base_url,
            headers={"Authorization": f"Bearer {settings.api_token}", "Content-Type": "application/json"},
            timeout=settings.timeout_seconds,
            transport=transport,
            follow_redirects=False,
        )

    @staticmethod
    def _document(payload: dict[str, Any]) -> ZapSignDocument:
        signers = payload.get("signers") or []
        signer_token = str(signers[0].get("token")) if signers and signers[0].get("token") else None
        token = payload.get("token")
        if not token:
            raise ZapSignUnavailableError("Resposta inválida do serviço de assinatura.")
        return ZapSignDocument(
            token=str(token), status=str(payload.get("status") or "pending"), signer_token=signer_token,
            signed_file=str(payload["signed_file"]) if payload.get("signed_file") else None,
        )

    def create_document(self, *, name: str, markdown_text: str, external_id: str, signer_name: str, signer_email: str) -> ZapSignDocument:
        payload = {
            "name": name,
            "markdown_text": markdown_text,
            "external_id": external_id,
            "lang": "pt-br",
            "disable_signers_get_original_file": True,
            "signers": [{
                "name": signer_name,
                "email": signer_email,
                "auth_mode": "tokenEmail",
                "send_automatic_email": True,
                "lock_email": True,
            }],
        }
        try:
            response = self._client.post("/docs/", json=payload)
            response.raise_for_status()
            return self._document(response.json())
        except ZapSignUnavailableError:
            raise
        except (httpx.HTTPError, TypeError, ValueError) as exc:
            raise ZapSignUnavailableError("Não foi possível enviar a prescrição para assinatura.") from exc

    def get_document(self, token: str) -> ZapSignDocument:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self._client.get(f"/docs/{token}/")
                if response.status_code == 429 or response.status_code >= 500:
                    raise httpx.HTTPStatusError("retryable response", request=response.request, response=response)
                response.raise_for_status()
                return self._document(response.json())
            except ZapSignUnavailableError:
                raise
            except (httpx.HTTPError, TypeError, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    sleep(0.05 * (2**attempt))
        raise ZapSignUnavailableError("Não foi possível consultar a assinatura agora.") from last_error

