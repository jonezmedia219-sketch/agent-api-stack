from unittest.mock import AsyncMock, patch


async def _deep_batch_fetch(url: str):
    mapping = {
        "https://example.com/": (
            """
            <html><head>
              <title>Example Inc | SaaS Growth Platform</title>
              <meta name='description' content='Example Inc helps revenue teams automate outbound and enrich company data.' />
              <meta property='og:site_name' content='Example Inc' />
            </head><body>
              <a href='/about'>About</a>
              <a href='/contact'>Contact</a>
              <a href='/careers'>Careers</a>
              <a href='/pricing'>Pricing</a>
              <a href='/developers'>API Docs</a>
              <p>Email hello@example.com</p>
            </body></html>
            """,
            "text/html",
            "https://example.com/",
        ),
        "https://example.com/contact": (
            """
            <html><body>
              <h1>Contact</h1>
              <p>Email sales@example.com</p>
              <p>Call +1 (555) 123-4567</p>
            </body></html>
            """,
            "text/html",
            "https://example.com/contact",
        ),
        "https://example.com/about": (
            """
            <html><body>
              <h1>About Example Inc</h1>
              <p>Example Inc builds workflow automation software.</p>
            </body></html>
            """,
            "text/html",
            "https://example.com/about",
        ),
        "https://example.com/careers": (
            "<html><body><h1>Careers</h1></body></html>",
            "text/html",
            "https://example.com/careers",
        ),
        "https://example.com/pricing": (
            "<html><body><h1>Pricing</h1></body></html>",
            "text/html",
            "https://example.com/pricing",
        ),
        "https://acme.co/": (
            """
            <html><head>
              <title>Acme Co</title>
              <meta name='description' content='Acme builds marketing automation software.' />
            </head><body>
              <a href='/support'>Contact</a>
              <p>Email team@acme.co</p>
            </body></html>
            """,
            "text/html",
            "https://acme.co/",
        ),
        "https://acme.co/support": (
            "<html><body><h1>Support</h1><p>Email team@acme.co</p></body></html>",
            "text/html",
            "https://acme.co/support",
        ),
    }
    return mapping[url]


def test_company_enrich_deep_batch_returns_multiple_result_items(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(side_effect=_deep_batch_fetch)):
        response = client.post("/api/v1/company-enrich/deep/batch", json={"domains": ["example.com", "acme.co"]})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["count"] == 2
    assert data["success_count"] == 2
    assert data["error_count"] == 0
    assert len(data["results"]) == 2
    assert data["results"][0]["ok"] is True
    assert data["results"][0]["data"]["domain"] == "example.com"
    assert data["results"][1]["ok"] is True
    assert data["results"][1]["data"]["domain"] == "acme.co"


def test_company_enrich_deep_batch_returns_partial_success_for_mixed_domains(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(side_effect=_deep_batch_fetch)):
        response = client.post("/api/v1/company-enrich/deep/batch", json={"domains": ["example.com", "bad domain"]})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["count"] == 2
    assert data["success_count"] == 1
    assert data["error_count"] == 1
    assert data["results"][0]["ok"] is True
    assert data["results"][1] == {
        "domain": "bad domain",
        "ok": False,
        "data": None,
        "error": {
            "code": "INVALID_INPUT",
            "message": "A valid domain is required.",
            "retryable": False,
        },
    }


def test_company_enrich_deep_batch_empty_list_returns_invalid_input(client):
    response = client.post("/api/v1/company-enrich/deep/batch", json={"domains": []})
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] in {"REQUEST_VALIDATION_ERROR", "VALIDATION_ERROR"}


def test_company_enrich_deep_batch_over_cap_returns_invalid_input(client):
    response = client.post("/api/v1/company-enrich/deep/batch", json={"domains": [f"site{i}.com" for i in range(11)]})
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] in {"REQUEST_VALIDATION_ERROR", "VALIDATION_ERROR"}


def test_company_enrich_deep_batch_endpoint_is_listed_in_tools(client):
    response = client.get("/tools")
    assert response.status_code == 200
    tools = response.json()["data"]["tools"]
    entry = next(item for item in tools if item["pricing_id"] == "company.enrich.deep.batch")
    assert entry["endpoint"] == "/api/v1/company-enrich/deep/batch"
    assert entry["method"] == "POST"
    assert entry["payment_required"] is True
    assert entry["payment_format"] == "base-usdc-onchain-v1"
    assert entry["expected_inputs"] == {"json_body": {"domains": "array<string> (max 10)"}}


def test_company_enrich_deep_batch_pricing_metadata_exists(client):
    response = client.get("/pricing")
    assert response.status_code == 200
    endpoints = response.json()["data"]["endpoints"]
    entry = next(item for item in endpoints if item["pricing_id"] == "company.enrich.deep.batch")
    assert entry == {
        "pricing_id": "company.enrich.deep.batch",
        "method": "POST",
        "path": "/api/v1/company-enrich/deep/batch",
        "payment_required": True,
        "payment_mode": "per_request",
        "chain": "base",
        "token": "USDC",
        "amount": "0.20",
        "receiver_wallet": "0xa850773dDdAc7051c9434E3b1e804531C12d265c",
        "payment_format": "base-usdc-onchain-v1",
    }


def test_company_enrich_deep_batch_discovery_is_paid(client):
    response = client.get("/tools")
    tools = response.json()["data"]["tools"]
    deep_batch_tool = next(item for item in tools if item["pricing_id"] == "company.enrich.deep.batch")
    assert deep_batch_tool["payment_required"] is True
    assert deep_batch_tool["payment_format"] == "base-usdc-onchain-v1"


def test_company_enrich_deep_batch_includes_pages_analyzed_for_multi_page_analysis(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(side_effect=_deep_batch_fetch)):
        response = client.post("/api/v1/company-enrich/deep/batch", json={"domains": ["example.com"]})

    assert response.status_code == 200
    result = response.json()["data"]["results"][0]
    assert result["ok"] is True
    assert result["data"]["pages_analyzed"] == [
        "https://example.com/",
        "https://example.com/contact",
        "https://example.com/about",
        "https://example.com/careers",
        "https://example.com/pricing",
    ]
