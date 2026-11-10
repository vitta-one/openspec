"""Contract tests for server-only provider adapters; no external network is used."""

from datetime import date
import json

import httpx
import pytest

from vitta_one.integrations.asaas import AsaasClient, cents_to_decimal
from vitta_one.integrations.cloudinary import CloudinaryClient
from vitta_one.integrations.settings import (
    AsaasSettings, CloudinarySettings, IntegrationConfigurationError,
    ZapSignSettings, asaas_settings, integration_status,
)
from vitta_one.integrations.zapsign import ZapSignClient


def test_cloudinary_uses_signed_authenticated_upload_and_private_download() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={
            "asset_id": "asset-1", "public_id": "vitta-one/clinical/random",
            "version": 123, "resource_type": "raw", "format": "pdf", "bytes": 4,
        })

    settings = CloudinarySettings("clinic-cloud", "public-key", "top-secret")
    client = CloudinaryClient(settings, transport=httpx.MockTransport(handler))
    asset = client.upload(content=b"%PDF", filename="exame.pdf", public_id="random")

    assert asset.asset_id == "asset-1"
    body = captured[0].content.decode("latin-1")
    assert "authenticated" in body
    assert "signature" in body
    assert "top-secret" not in body

    url = client.private_download_url(public_id=asset.public_id, format="pdf", resource_type="raw")
    assert url.startswith("https://api.cloudinary.com/v1_1/clinic-cloud/raw/download?")
    assert "signature=" in url and "expires_at=" in url
    assert "top-secret" not in url


def test_zapsign_payload_matches_document_contract_without_exposing_token() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={
            "token": "doc-token", "status": "pending",
            "signers": [{"token": "signer-token"}], "signed_file": None,
        })

    settings = ZapSignSettings("api-secret", "webhook-secret", base_url="https://api.zapsign.com.br/api/v1")
    client = ZapSignClient(settings, transport=httpx.MockTransport(handler))
    result = client.create_document(
        name="Prescrição 1", markdown_text="# Prescrição", external_id="vitta-prescription-1",
        signer_name="Dra. Teste", signer_email="medica@example.com",
    )

    assert result.token == "doc-token"
    request = captured[0]
    assert request.headers["authorization"] == "Bearer api-secret"
    payload = json.loads(request.content)
    assert payload["external_id"] == "vitta-prescription-1"
    assert payload["markdown_text"] == "# Prescrição"
    assert payload["signers"][0]["auth_mode"] == "tokenEmail"
    assert "sandbox" not in payload


def test_asaas_uses_sandbox_headers_exact_money_and_external_reference() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path.endswith("/payments") and request.method == "POST":
            return httpx.Response(200, json={"id": "pay-1", "status": "PENDING", "invoiceUrl": "https://sandbox.example/invoice"})
        return httpx.Response(200, json={"data": []})

    client = AsaasClient(
        AsaasSettings("sandbox-key", "webhook-secret"),
        transport=httpx.MockTransport(handler),
    )
    charge = client.create_charge(
        customer_id="cus-1", billing_type="PIX", value_cents=12990,
        due_date=date(2026, 11, 30), description="Consulta", external_reference="vitta-account-1",
    )

    assert charge.id == "pay-1"
    request = captured[0]
    assert request.url.host == "api-sandbox.asaas.com"
    assert request.headers["access_token"] == "sandbox-key"
    assert request.headers["user-agent"] == "Vitta-One/1.0"
    assert json.loads(request.content)["value"] == "129.90"
    assert cents_to_decimal(1) == "0.01"


def test_asaas_customer_payload_includes_required_cpf_without_logging_secret() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"id": "cus-1"})

    client = AsaasClient(
        AsaasSettings("sandbox-key", "webhook-secret"),
        transport=httpx.MockTransport(handler),
    )
    customer = client.create_customer(
        name="Paciente Sintético",
        cpf_cnpj="12345678901",
        external_reference="vitta-patient-1",
    )

    assert customer.id == "cus-1"
    payload = json.loads(captured[0].content)
    assert payload == {
        "name": "Paciente Sintético",
        "cpfCnpj": "12345678901",
        "externalReference": "vitta-patient-1",
    }


def test_settings_reject_partial_credentials_and_unapproved_production(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("ASAAS_API_KEY", "ASAAS_WEBHOOK_TOKEN", "ASAAS_API_BASE_URL", "VITTA_ONE_ALLOW_ASAAS_PRODUCTION"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ASAAS_API_KEY", "only-one")
    with pytest.raises(IntegrationConfigurationError):
        asaas_settings()

    monkeypatch.setenv("ASAAS_WEBHOOK_TOKEN", "webhook")
    monkeypatch.setenv("ASAAS_API_BASE_URL", "https://api.asaas.com/v3")
    with pytest.raises(IntegrationConfigurationError):
        asaas_settings()

    assert integration_status()["asaas"] == "INVALID_CONFIGURATION"

