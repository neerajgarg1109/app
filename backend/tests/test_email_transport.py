"""Transport checks never send real mail or read production credentials."""
import asyncio
import json

import httpx
import pytest

import email_transport


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "resend")
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "hello@example.com")
    monkeypatch.setenv("EMAIL_FROM_NAME", "CardIQ")
    monkeypatch.delenv("EMAIL_REPLY_TO", raising=False)


def run_delivery():
    return asyncio.run(email_transport.deliver_email(
        to="reader@example.com", subject="Your recommendation", html="<p>Result</p>"))


def mock_provider(monkeypatch, handler):
    client_class = httpx.AsyncClient
    monkeypatch.setattr(email_transport.httpx, "AsyncClient", lambda **kwargs:
                        client_class(transport=httpx.MockTransport(handler), **kwargs))


def test_direct_provider_request_and_message_id(configured, monkeypatch):
    monkeypatch.setenv("EMAIL_REPLY_TO", "support@example.com")
    def handler(request):
        assert str(request.url) == "https://api.resend.com/emails"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert json.loads(request.content) == {
            "from": "CardIQ <hello@example.com>", "to": ["reader@example.com"],
            "subject": "Your recommendation", "html": "<p>Result</p>",
            "reply_to": "support@example.com",
        }
        return httpx.Response(200, json={"id": "email-123"})
    mock_provider(monkeypatch, handler)
    assert run_delivery() == "email-123"


@pytest.mark.parametrize("key,value", [
    ("EMAIL_PROVIDER", "disabled"), ("EMAIL_PROVIDER", "unknown"),
    ("RESEND_API_KEY", ""), ("EMAIL_FROM_ADDRESS", ""),
])
def test_missing_configuration_never_contacts_provider(configured, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    def unexpected(**kwargs):
        pytest.fail("Unconfigured delivery must not contact a provider")
    monkeypatch.setattr(email_transport.httpx, "AsyncClient", unexpected)
    with pytest.raises(email_transport.EmailConfigurationError):
        run_delivery()


@pytest.mark.parametrize("response", [
    httpx.Response(401, json={"message": "provider-secret"}),
    httpx.Response(429, json={"message": "rate limited"}),
    httpx.Response(500, text="provider error"),
    httpx.Response(200, json={}),
    httpx.Response(200, text="invalid json"),
    httpx.Response(302, headers={"Location": "https://other.example"}),
])
def test_provider_failures_do_not_report_success_or_leak_response(configured, monkeypatch, response):
    mock_provider(monkeypatch, lambda request: response)
    with pytest.raises(email_transport.EmailDeliveryError) as error:
        run_delivery()
    assert "provider-secret" not in str(error.value)


def test_timeout_is_delivery_failure(configured, monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("test-key", request=request)
    mock_provider(monkeypatch, handler)
    with pytest.raises(email_transport.EmailDeliveryError, match="Email delivery failed"):
        run_delivery()


@pytest.mark.parametrize("failure,status", [
    (email_transport.EmailConfigurationError, 503),
    (email_transport.EmailDeliveryError, 502),
])
def test_api_email_helper_reports_transport_failure(monkeypatch, failure, status):
    import server
    async def fail(**kwargs):
        raise failure("private-provider-details")
    monkeypatch.setattr(server, "deliver_email", fail)
    with pytest.raises(server.HTTPException) as error:
        asyncio.run(server.send_email(to="reader@example.com", subject="Result", html="<p>Result</p>"))
    assert error.value.status_code == status
    assert "private-provider-details" not in error.value.detail
