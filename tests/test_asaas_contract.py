"""HTTP contract tests; these do not constitute real Sandbox verification."""
from datetime import date
from decimal import Decimal
import json

import httpx
import pytest

from vitta_one.financial.asaas import AsaasClient, ConfigurationError, FinancialError, ProviderUnknown, amount, payment_url


@pytest.mark.parametrize("value", [0, -1, "NaN", "Infinity", "1.001", "oops", "10000000000"])
def test_invalid_money(value):
    with pytest.raises(FinancialError):
        amount(value)


def test_payment_contract_no_card_data_or_production():
    seen = []
    def handle(request):
        seen.append(request)
        assert request.headers["access_token"] == "test-only"
        assert request.headers["user-agent"] == "Vitta-One/1.0"
        assert request.url.host == "api-sandbox.asaas.com"
        assert json.loads(request.content) == {"customer": "cus_test", "billingType": "PIX", "value": 12.34,
                                              "dueDate": "2026-12-01", "externalReference": "local-id"}
        return httpx.Response(200, json={"id": "pay_test", "status": "PENDING", "value": 12.34})
    result = AsaasClient("test-only", transport=httpx.MockTransport(handle)).create_payment(
        customer_id="cus_test", billing_type="PIX", value=Decimal("12.34"), due_date=date(2026, 12, 1), reference="local-id")
    assert result["value"] == Decimal("12.34")
    assert len(seen) == 1


@pytest.mark.parametrize("key,url", [("", "https://api-sandbox.asaas.com/v3"), ("$aact_prod_x", "https://api-sandbox.asaas.com/v3"), ("test", "https://api.asaas.com/v3")])
def test_bad_configuration_blocked(key, url):
    with pytest.raises(ConfigurationError):
        AsaasClient(key, url)


@pytest.mark.parametrize("status", [302, 429, 500, 503])
def test_uncertain_response_never_retried(status):
    seen = []
    def handle(request):
        seen.append(request)
        return httpx.Response(status)
    with pytest.raises(ProviderUnknown):
        AsaasClient("test", transport=httpx.MockTransport(handle)).refund("pay_test")
    assert len(seen) == 1


def test_timeout_not_retried():
    seen = []
    def handle(request):
        seen.append(request)
        raise httpx.ReadTimeout("test only")
    with pytest.raises(ProviderUnknown):
        AsaasClient("test", transport=httpx.MockTransport(handle)).cancel("pay_test")
    assert len(seen) == 1


def test_paginated_lookup_checks_reference():
    def handle(request):
        offset = int(request.url.params["offset"])
        return httpx.Response(200, json={"hasMore": offset == 0, "data": [
            {"id": "cus_test", "externalReference": "match" if offset else "other"}]})
    assert len(AsaasClient("test", transport=httpx.MockTransport(handle)).find("customers", "match")) == 1


@pytest.mark.parametrize("url", ["javascript:alert(1)", "http://sandbox.asaas.com/a", "https://sandbox.asaas.com.evil.test/a", "https://user:secret@sandbox.asaas.com/a"])
def test_unsafe_payment_url(url):
    with pytest.raises(FinancialError):
        payment_url(url)
