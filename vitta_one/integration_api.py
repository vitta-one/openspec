"""Provider webhook routes composed into the existing Reflex backend."""
import json
import os
import secrets
from datetime import datetime

import reflex as rx
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import select
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from svix.webhooks import Webhook, WebhookVerificationError

from vitta_one.models.financial import FinancialWebhookEvent
from vitta_one.models.notification import EmailWebhookEvent

MAX_BODY = 256 * 1024


async def limited_body(request: Request) -> bytes:
    body = bytearray()
    async for part in request.stream():
        body.extend(part)
        if len(body) > MAX_BODY:
            raise OverflowError
    return bytes(body)


async def asaas_endpoint(request: Request):
    expected = os.getenv("ASAAS_WEBHOOK_TOKEN", "")
    if not 32 <= len(expected) <= 255 or any(char.isspace() for char in expected):
        return JSONResponse({}, status_code=503)
    if not secrets.compare_digest(request.headers.get("asaas-access-token", "").encode(), expected.encode()):
        return JSONResponse({}, status_code=401)
    try:
        data = json.loads(await limited_body(request))
        event_id, kind, payment_id = data["id"], data["event"], data["payment"]["id"]
        if not all(isinstance(v, str) and 1 <= len(v) <= maxlen for v, maxlen in [(event_id, 180), (kind, 80), (payment_id, 128)]):
            raise ValueError
    except OverflowError:
        return JSONResponse({}, status_code=413)
    except (ValueError, KeyError, TypeError):
        return JSONResponse({}, status_code=400)
    try:
        with rx.session() as db:
            exists = db.exec(select(FinancialWebhookEvent.id).where(FinancialWebhookEvent.event_id == event_id)).first()
            if not exists:
                db.add(FinancialWebhookEvent(event_id=event_id, event_type=kind, payment_id=payment_id))
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    if not db.exec(select(FinancialWebhookEvent.id).where(FinancialWebhookEvent.event_id == event_id)).first():
                        raise
    except SQLAlchemyError:
        return JSONResponse({}, status_code=503)
    return JSONResponse({"received": True}, status_code=200)


async def resend_endpoint(request: Request):
    secret = os.getenv("RESEND_WEBHOOK_SECRET", "")
    if not secret:
        return JSONResponse({}, status_code=503)
    try:
        raw = await limited_body(request)
        Webhook(secret).verify(raw, dict(request.headers))
        data = json.loads(raw)
        event_id, kind, message_id = request.headers["svix-id"], data["type"], data["data"]["email_id"]
        if not all(isinstance(v, str) and 1 <= len(v) <= maxlen for v, maxlen in [(event_id, 180), (kind, 64), (message_id, 128)]):
            raise ValueError
        occurred = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        if occurred.tzinfo is None:
            raise ValueError
    except OverflowError:
        return JSONResponse({}, status_code=413)
    except (WebhookVerificationError, ValueError, KeyError, TypeError):
        return JSONResponse({}, status_code=400)
    try:
        with rx.session() as db:
            if not db.exec(select(EmailWebhookEvent.id).where(EmailWebhookEvent.event_id == event_id)).first():
                db.add(EmailWebhookEvent(event_id=event_id, event_type=kind, message_id=message_id, occurred_at=occurred))
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    if not db.exec(select(EmailWebhookEvent.id).where(EmailWebhookEvent.event_id == event_id)).first():
                        raise
    except SQLAlchemyError:
        return JSONResponse({}, status_code=503)
    return JSONResponse({"received": True}, status_code=200)


provider_routes = [Route("/api/webhooks/asaas", asaas_endpoint, methods=["POST"]),
                   Route("/api/webhooks/resend", resend_endpoint, methods=["POST"])]
