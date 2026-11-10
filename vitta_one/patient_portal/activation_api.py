"""Small native endpoints mounted inside the Reflex ASGI application."""

import hmac
import json
from urllib.parse import parse_qs

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from vitta_one.patient_portal.service import (
    PatientPortalActivationError,
    activate_patient_account,
)
from vitta_one.digital_signature.service import SignatureError, process_zapsign_webhook
from vitta_one.finance.service import FinanceError, process_asaas_webhook
from vitta_one.integrations.settings import (
    IntegrationConfigurationError,
    asaas_settings,
    zapsign_settings,
)

_NO_STORE = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
}
_API_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}
_GENERIC_FAILURE = (
    "<!doctype html><html lang='pt-BR'><meta charset='utf-8'>"
    "<title>Ativação não concluída</title><main><h1>Não foi possível ativar o acesso</h1>"
    "<p>Confira os dados ou solicite um novo convite à Recepção.</p>"
    "<a href='/ativar-paciente'>Tentar novamente</a></main></html>"
)
_SUCCESS = (
    "<!doctype html><html lang='pt-BR'><meta charset='utf-8'>"
    "<title>Acesso ativado</title><main><h1>Acesso ativado</h1>"
    "<p>Agora entre com seu e-mail e a senha escolhida.</p>"
    "<a href='/login'>Ir para o login</a></main></html>"
)


async def activate_patient_endpoint(request: Request) -> HTMLResponse:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/x-www-form-urlencoded":
        return HTMLResponse(_GENERIC_FAILURE, status_code=400, headers=_NO_STORE)

    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 4096:
            return HTMLResponse(_GENERIC_FAILURE, status_code=400, headers=_NO_STORE)
        chunks.append(chunk)
    try:
        values = parse_qs(b"".join(chunks).decode("utf-8"), keep_blank_values=True, strict_parsing=True)
    except (UnicodeDecodeError, ValueError):
        return HTMLResponse(_GENERIC_FAILURE, status_code=400, headers=_NO_STORE)
    if set(values) != {"email", "code", "password"} or any(len(items) != 1 for items in values.values()):
        return HTMLResponse(_GENERIC_FAILURE, status_code=400, headers=_NO_STORE)

    try:
        import reflex as rx

        with rx.session() as db:
            activate_patient_account(
                db,
                email=values["email"][0],
                code=values["code"][0],
                password=values["password"][0],
            )
    except PatientPortalActivationError:
        return HTMLResponse(_GENERIC_FAILURE, status_code=400, headers=_NO_STORE)
    except Exception:
        # Intentionally omit exception and submitted fields from response/log payload.
        return HTMLResponse(_GENERIC_FAILURE, status_code=500, headers=_NO_STORE)
    return HTMLResponse(_SUCCESS, status_code=200, headers=_NO_STORE)


async def _json_body(request: Request) -> dict:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise ValueError("invalid content type")
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 256 * 1024:
            raise ValueError("payload too large")
        chunks.append(chunk)
    payload = json.loads(b"".join(chunks).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("invalid payload")
    return payload


def _bearer(request: Request) -> str:
    value = request.headers.get("authorization", "")
    return value[7:] if value.startswith("Bearer ") else ""


async def zapsign_webhook_endpoint(request: Request) -> JSONResponse:
    try:
        settings = zapsign_settings()
        if settings is None:
            return JSONResponse({"detail": "Integração indisponível."}, status_code=503, headers=_API_HEADERS)
        if not hmac.compare_digest(_bearer(request), settings.webhook_token):
            return JSONResponse({"detail": "Não autorizado."}, status_code=401, headers=_API_HEADERS)
        payload = await _json_body(request)
        import reflex as rx
        with rx.session() as db:
            outcome = process_zapsign_webhook(db, payload)
        return JSONResponse({"status": "accepted", "outcome": outcome}, status_code=200, headers=_API_HEADERS)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError, SignatureError):
        return JSONResponse({"detail": "Payload inválido."}, status_code=400, headers=_API_HEADERS)
    except IntegrationConfigurationError:
        return JSONResponse({"detail": "Integração indisponível."}, status_code=503, headers=_API_HEADERS)
    except Exception:
        return JSONResponse({"detail": "Não foi possível processar o evento."}, status_code=500, headers=_API_HEADERS)


async def asaas_webhook_endpoint(request: Request) -> JSONResponse:
    try:
        settings = asaas_settings()
        if settings is None:
            return JSONResponse({"detail": "Integração indisponível."}, status_code=503, headers=_API_HEADERS)
        supplied = request.headers.get("asaas-access-token", "")
        if not hmac.compare_digest(supplied, settings.webhook_token):
            return JSONResponse({"detail": "Não autorizado."}, status_code=401, headers=_API_HEADERS)
        payload = await _json_body(request)
        import reflex as rx
        with rx.session() as db:
            outcome = process_asaas_webhook(db, payload)
        return JSONResponse({"status": "accepted", "outcome": outcome}, status_code=200, headers=_API_HEADERS)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError, FinanceError):
        return JSONResponse({"detail": "Payload inválido."}, status_code=400, headers=_API_HEADERS)
    except IntegrationConfigurationError:
        return JSONResponse({"detail": "Integração indisponível."}, status_code=503, headers=_API_HEADERS)
    except Exception:
        return JSONResponse({"detail": "Não foi possível processar o evento."}, status_code=500, headers=_API_HEADERS)


activation_api = Starlette(
    routes=[
        Route("/api/paciente/ativar", activate_patient_endpoint, methods=["POST"]),
        Route("/api/webhooks/zapsign", zapsign_webhook_endpoint, methods=["POST"]),
        Route("/api/webhooks/asaas", asaas_webhook_endpoint, methods=["POST"]),
    ],
    debug=False,
)

