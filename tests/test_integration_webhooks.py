"""ASGI webhook authentication and response-hardening tests."""

from contextlib import nullcontext
from types import SimpleNamespace

from starlette.testclient import TestClient

from vitta_one.patient_portal import activation_api as webhook_module


def test_zapsign_webhook_rejects_invalid_token_without_processing(monkeypatch) -> None:
    monkeypatch.setattr(
        webhook_module,
        "zapsign_settings",
        lambda: SimpleNamespace(webhook_token="expected-token"),
    )
    called = []
    monkeypatch.setattr(webhook_module, "process_zapsign_webhook", lambda *args: called.append(args))

    response = TestClient(webhook_module.activation_api).post(
        "/api/webhooks/zapsign",
        headers={"Authorization": "Bearer wrong-token"},
        json={"event_type": "doc_signed", "token": "doc-1"},
    )

    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"
    assert called == []


def test_asaas_webhook_accepts_authenticated_json_and_returns_generic_outcome(monkeypatch) -> None:
    monkeypatch.setattr(
        webhook_module,
        "asaas_settings",
        lambda: SimpleNamespace(webhook_token="webhook-token"),
    )
    monkeypatch.setattr(webhook_module, "process_asaas_webhook", lambda db, payload: "PROCESSED")

    import reflex as rx

    monkeypatch.setattr(rx, "session", lambda: nullcontext(object()))
    response = TestClient(webhook_module.activation_api).post(
        "/api/webhooks/asaas",
        headers={"asaas-access-token": "webhook-token"},
        json={"id": "evt-1", "event": "PAYMENT_RECEIVED", "payment": {"id": "pay-1"}},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "outcome": "PROCESSED"}
    assert response.headers["cache-control"] == "no-store"


def test_webhooks_reject_non_json_content_type(monkeypatch) -> None:
    monkeypatch.setattr(
        webhook_module,
        "asaas_settings",
        lambda: SimpleNamespace(webhook_token="webhook-token"),
    )
    response = TestClient(webhook_module.activation_api).post(
        "/api/webhooks/asaas",
        headers={"asaas-access-token": "webhook-token", "content-type": "text/plain"},
        content=b"not-json",
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Payload inválido."}
