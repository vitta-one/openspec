"""Native form activation endpoint mounted inside the Reflex ASGI application."""

from urllib.parse import parse_qs

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from vitta_one.patient_portal.service import (
    PatientPortalActivationError,
    activate_patient_account,
)

_NO_STORE = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
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


activation_api = Starlette(
    routes=[Route("/api/paciente/ativar", activate_patient_endpoint, methods=["POST"])],
    debug=False,
)
