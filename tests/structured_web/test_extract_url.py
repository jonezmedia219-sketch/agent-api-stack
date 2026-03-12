from unittest.mock import AsyncMock, patch


def test_extract_url_success(client, article_html):
    with patch("app.services.structured_web.service.fetch_html", new=AsyncMock(return_value=(article_html, "text/html"))):
        response = client.post(
            "/api/v1/structured-web/extract",
            json={"url": "https://example.com/blog/ai-agents-for-workflows"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["url"] == "https://example.com/blog/ai-agents-for-workflows"
    assert body["data"]["title"] == "AI Agents for Workflows"
    assert body["data"]["links"][0]["href"] == "https://example.com/related"


def test_extract_url_invalid_url(client):
    response = client.post(
        "/api/v1/structured-web/extract",
        json={"url": "notaurl"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "REQUEST_VALIDATION_ERROR"
