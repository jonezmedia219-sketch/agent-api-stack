from unittest.mock import AsyncMock, patch


def test_free_endpoint_without_payment_still_works(client):
    response = client.get("/api/v1/search", params={"q": "agent infrastructure", "source": "mock"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True


def test_paid_endpoint_shadow_mode_does_not_block(client, company_contact_html):
    client.app.state.payment_shadow_mode = True
    client.app.state.payment_hard_enforcement = False

    with patch("app.services.lead_extract.service.fetch_html", new=AsyncMock(return_value=(company_contact_html, "text/html"))):
        response = client.post(
            "/api/v1/lead-extract",
            json={"url": "https://acmegrowth.com/contact"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True


def test_paid_endpoint_hard_enforcement_returns_402_without_payment(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True

    response = client.post(
        "/api/v1/lead-extract",
        json={"html": "<html><body><h1>Acme</h1></body></html>", "source_url": "https://acme.com"},
    )

    assert response.status_code == 402
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "PAYMENT_REQUIRED"
    assert body["meta"]["pricing_id"] == "lead_extract.html"
    assert body["payment"]["chain"] == "base"
    assert body["payment"]["token"] == "USDC"
    assert body["payment"]["receiver_wallet"] == "0xa850773dDdAc7051c9434E3b1e804531C12d265c"
    assert body["payment"]["payment_mode"] == "per_request"


def test_paid_endpoint_succeeds_with_stub_payment_proof(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Debug-Payment": "ok"},
        json={"html": "<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>", "source_url": "https://acme.com"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "hello@acme.com" in body["data"]["emails"]


def test_usage_recording_only_happens_after_successful_execution(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True

    with patch("app.api.v1.lead_extract.record_usage") as record_usage_mock:
        response = client.post(
            "/api/v1/lead-extract",
            json={"html": "<html><body><h1>Blocked</h1></body></html>", "source_url": "https://blocked.com"},
        )

    assert response.status_code == 402
    record_usage_mock.assert_not_called()
