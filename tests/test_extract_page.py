from unittest.mock import patch

from app.models.extract_page import ExtractPageData
from app.services.extract_page.service import ExtractPageError


def test_extract_page_returns_structured_data_for_valid_mocked_html(client):
    mocked = ExtractPageData(
        url="https://example.com",
        final_url="https://example.com/final",
        title="Acme Pricing",
        summary="Acme helps teams automate outreach.",
        emails=["hello@acme.com"],
        phone_numbers=["(555) 123-4567"],
        social_links=["https://www.linkedin.com/company/acme"],
        important_links=["https://example.com/contact", "https://example.com/pricing"],
        text_excerpt="Acme helps teams automate outreach and enrich websites into structured data.",
    )

    with patch("app.api.v1.extract_page.extract_page_from_url", return_value=mocked):
        response = client.post("/api/v1/extract/page", json={"url": "https://example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["url"] == "https://example.com"
    assert body["data"]["final_url"] == "https://example.com/final"
    assert body["data"]["title"] == "Acme Pricing"
    assert body["data"]["summary"] == "Acme helps teams automate outreach."
    assert body["data"]["emails"] == ["hello@acme.com"]
    assert body["data"]["phone_numbers"] == ["(555) 123-4567"]
    assert body["data"]["social_links"] == ["https://www.linkedin.com/company/acme"]
    assert body["data"]["important_links"] == ["https://example.com/contact", "https://example.com/pricing"]
    assert "text_excerpt" in body["data"]


def test_extract_page_invalid_url_returns_invalid_input(client):
    response = client.post("/api/v1/extract/page", json={"url": "not-a-url"})

    assert response.status_code == 400
    body = response.json()
    assert body == {
        "ok": False,
        "error": {
            "code": "INVALID_INPUT",
            "message": "A valid URL is required.",
            "retryable": False,
        },
    }


def test_extract_page_surfaces_fetch_errors(client):
    with patch(
        "app.api.v1.extract_page.extract_page_from_url",
        side_effect=ExtractPageError(code="FETCH_FAILED", message="Unable to fetch the requested URL.", status_code=502, retryable=True),
    ):
        response = client.post("/api/v1/extract/page", json={"url": "https://example.com"})

    assert response.status_code == 502
    assert response.json() == {
        "ok": False,
        "error": {
            "code": "FETCH_FAILED",
            "message": "Unable to fetch the requested URL.",
            "retryable": True,
        },
    }
