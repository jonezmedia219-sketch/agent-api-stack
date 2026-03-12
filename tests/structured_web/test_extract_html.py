def test_extract_html_success(client, article_html):
    response = client.post(
        "/api/v1/structured-web/extract-html",
        json={
            "html": article_html,
            "source_url": "https://example.com/blog/ai-agents-for-workflows",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["title"] == "AI Agents for Workflows"
    assert body["data"]["author"] == "Jane Smith"
    assert body["data"]["published_date"] == "2026-02-10"
    assert body["data"]["content_type"] == "article"
    assert "automate repetitive business tasks" in body["data"]["main_text"]
    assert body["data"]["metadata"]["site_name"] == "Example Site"
    assert body["meta"]["api"] == "structured_web"


def test_extract_html_validation_error(client):
    response = client.post(
        "/api/v1/structured-web/extract-html",
        json={"html": "   "},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] in {"REQUEST_VALIDATION_ERROR", "VALIDATION_ERROR"}
