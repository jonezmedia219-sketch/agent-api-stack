from unittest.mock import AsyncMock, patch


def test_lead_extract_html_success(client, company_contact_html):
    response = client.post(
        "/api/v1/lead-extract",
        json={
            "html": company_contact_html,
            "source_url": "https://acmegrowth.com/contact",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    data = body["data"]
    assert "hello@acmegrowth.com" in data["emails"]
    assert "+1 (555) 123-4567" in data["phone_numbers"]
    assert data["company_name"] == "Acme Growth Partners"
    assert data["contact_forms_detected"] is True
    assert any("linkedin.com" in link for link in data["social_media_links"])
    assert any("Austin, TX 78701" in address for address in data["addresses"])


def test_lead_extract_url_success(client, company_contact_html):
    with patch("app.services.lead_extract.service.fetch_html", new=AsyncMock(return_value=(company_contact_html, "text/html"))):
        response = client.post(
            "/api/v1/lead-extract",
            json={"url": "https://acmegrowth.com/contact"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["source_url"] == "https://acmegrowth.com/contact"


def test_lead_extract_requires_url_or_html(client):
    response = client.post("/api/v1/lead-extract", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] in {"REQUEST_VALIDATION_ERROR", "VALIDATION_ERROR"}
