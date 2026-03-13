from unittest.mock import AsyncMock, patch


async def _batch_fetch(url: str):
    mapping = {
        "https://example.com/": (
            """
            <html><head>
              <title>Example Inc | SaaS Growth Platform</title>
              <meta name='description' content='Example Inc helps revenue teams automate outbound.' />
              <meta property='og:site_name' content='Example Inc' />
            </head><body>
              <a href='/about'>About</a>
              <a href='/contact'>Contact</a>
              <a href='/careers'>Careers</a>
              <a href='/pricing'>Pricing</a>
              <p>Email hello@example.com</p>
            </body></html>
            """,
            "text/html",
            "https://example.com/",
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
    }
    return mapping[url]


def test_company_enrich_batch_returns_multiple_result_items(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(side_effect=_batch_fetch)):
        response = client.post("/api/v1/company-enrich/batch", json={"domains": ["example.com", "acme.co"]})

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


def test_company_enrich_batch_returns_partial_success_for_mixed_domains(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(side_effect=_batch_fetch)):
        response = client.post("/api/v1/company-enrich/batch", json={"domains": ["example.com", "bad domain"]})

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


def test_company_enrich_batch_empty_list_returns_invalid_input(client):
    response = client.post("/api/v1/company-enrich/batch", json={"domains": []})
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] in {"REQUEST_VALIDATION_ERROR", "VALIDATION_ERROR"}


def test_company_enrich_batch_over_cap_returns_invalid_input(client):
    response = client.post("/api/v1/company-enrich/batch", json={"domains": [f"site{i}.com" for i in range(11)]})
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] in {"REQUEST_VALIDATION_ERROR", "VALIDATION_ERROR"}


def test_company_enrich_batch_endpoint_is_listed_in_tools(client):
    response = client.get("/tools")
    assert response.status_code == 200
    tools = response.json()["data"]["tools"]
    entry = next(item for item in tools if item["pricing_id"] == "company.enrich.batch")
    assert entry["endpoint"] == "/api/v1/company-enrich/batch"
    assert entry["method"] == "POST"
    assert entry["payment_required"] is True
    assert entry["payment_format"] == "base-usdc-onchain-v1"
    assert entry["expected_inputs"] == {"json_body": {"domains": "array<string> (max 10)"}}


def test_company_enrich_batch_pricing_metadata_exists(client):
    response = client.get("/pricing")
    assert response.status_code == 200
    endpoints = response.json()["data"]["endpoints"]
    entry = next(item for item in endpoints if item["pricing_id"] == "company.enrich.batch")
    assert entry == {
        "pricing_id": "company.enrich.batch",
        "method": "POST",
        "path": "/api/v1/company-enrich/batch",
        "payment_required": True,
        "payment_mode": "per_request",
        "chain": "base",
        "token": "USDC",
        "amount": "0.10",
        "receiver_wallet": "0xa850773dDdAc7051c9434E3b1e804531C12d265c",
        "payment_format": "base-usdc-onchain-v1",
    }


def test_company_enrich_batch_discovery_is_paid(client):
    response = client.get("/tools")
    tools = response.json()["data"]["tools"]
    batch_tool = next(item for item in tools if item["pricing_id"] == "company.enrich.batch")
    assert batch_tool["payment_required"] is True
    assert batch_tool["payment_format"] == "base-usdc-onchain-v1"
