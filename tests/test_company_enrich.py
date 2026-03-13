from unittest.mock import AsyncMock, patch


MOCK_HOMEPAGE_HTML = """
<html lang='en'>
  <head>
    <title>Example Inc | SaaS Growth Platform</title>
    <meta name='description' content='Example Inc helps revenue teams automate outbound and enrich company data.' />
    <meta property='og:site_name' content='Example Inc' />
  </head>
  <body>
    <nav>
      <a href='/about'>About</a>
      <a href='/contact'>Contact</a>
      <a href='/careers'>Careers</a>
      <a href='/pricing'>Pricing</a>
      <a href='https://www.linkedin.com/company/exampleinc'>LinkedIn</a>
    </nav>
    <main>
      <h1>Example Inc</h1>
      <p>Example Inc builds workflow automation software for modern sales teams.</p>
      <p>Reach us at hello@example.com or call +1 (555) 123-4567.</p>
      <p>Visit our HQ at 123 Main Street, Austin, TX 78701.</p>
    </main>
  </body>
</html>
"""


def test_company_enrich_returns_expected_fields_for_valid_mocked_html(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(return_value=(MOCK_HOMEPAGE_HTML, "text/html", "https://example.com/"))):
        response = client.post("/api/v1/company-enrich", json={"domain": "example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["domain"] == "example.com"
    assert data["normalized_url"] == "https://example.com/"
    assert data["company_name"] == "Example Inc"
    assert data["summary"]
    assert data["industry"] == "saas"
    assert data["emails"] == ["hello@example.com"]
    assert "+1 (555) 123-4567" in data["phone_numbers"]
    assert data["social_links"] == ["https://www.linkedin.com/company/exampleinc"]
    assert data["contact_page"] == "https://example.com/contact"
    assert data["about_page"] == "https://example.com/about"
    assert data["careers_page"] == "https://example.com/careers"
    assert data["pricing_page"] == "https://example.com/pricing"
    assert any("Austin, TX 78701" in address for address in data["addresses"])
    assert data["signals"] == {
        "has_contact_page": True,
        "has_about_page": True,
        "has_careers_page": True,
        "has_pricing_page": True,
        "has_api_docs": False,
        "has_blog": False,
        "has_login": False,
        "has_signup": False,
    }
    assert data["pages_analyzed"] == ["https://example.com/"]


def test_company_enrich_invalid_domain_returns_invalid_input(client):
    response = client.post("/api/v1/company-enrich", json={"domain": "not a domain"})

    assert response.status_code == 400
    assert response.json() == {
        "ok": False,
        "error": {
            "code": "INVALID_INPUT",
            "message": "A valid domain is required.",
            "retryable": False,
        },
    }


def test_company_enrich_detects_important_pages_from_homepage_links(client):
    html = """
    <html>
      <head><title>Acme</title></head>
      <body>
        <a href='/company'>About Us</a>
        <a href='/support'>Contact Support</a>
        <a href='/jobs'>Jobs</a>
        <a href='/plans'>Plans</a>
      </body>
    </html>
    """

    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(return_value=(html, "text/html", "https://acme.co/"))):
        response = client.post("/api/v1/company-enrich", json={"domain": "acme.co"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["about_page"] == "https://acme.co/company"
    assert data["contact_page"] == "https://acme.co/support"
    assert data["careers_page"] == "https://acme.co/jobs"
    assert data["pricing_page"] == "https://acme.co/plans"
    assert data["signals"]["has_about_page"] is True
    assert data["signals"]["has_contact_page"] is True
    assert data["signals"]["has_careers_page"] is True
    assert data["signals"]["has_pricing_page"] is True
    assert data["signals"]["has_api_docs"] is False
    assert data["pages_analyzed"] == ["https://acme.co/"]


def test_company_enrich_shallow_schema_names_are_correct(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(return_value=(MOCK_HOMEPAGE_HTML, "text/html", "https://example.com/"))):
        response = client.post("/api/v1/company-enrich", json={"domain": "example.com"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data.keys()) == {
        "domain",
        "normalized_url",
        "company_name",
        "summary",
        "industry",
        "emails",
        "phone_numbers",
        "social_links",
        "contact_page",
        "about_page",
        "careers_page",
        "pricing_page",
        "important_links",
        "addresses",
        "signals",
        "pages_analyzed",
    }
    assert set(data["signals"].keys()) == {
        "has_contact_page",
        "has_about_page",
        "has_careers_page",
        "has_pricing_page",
        "has_api_docs",
        "has_blog",
        "has_login",
        "has_signup",
    }


def test_company_enrich_endpoint_is_listed_in_tools(client):
    response = client.get("/tools")
    assert response.status_code == 200
    tools = response.json()["data"]["tools"]
    entry = next(item for item in tools if item["pricing_id"] == "company.enrich")
    assert entry["endpoint"] == "/api/v1/company-enrich"
    assert entry["method"] == "POST"
    assert entry["payment_required"] is True
    assert entry["payment_format"] == "base-usdc-onchain-v1"
    assert entry["expected_inputs"] == {"json_body": {"domain": "string"}}


def test_company_enrich_pricing_metadata_exists(client):
    response = client.get("/pricing")
    assert response.status_code == 200
    endpoints = response.json()["data"]["endpoints"]
    entry = next(item for item in endpoints if item["pricing_id"] == "company.enrich")
    assert entry == {
        "pricing_id": "company.enrich",
        "method": "POST",
        "path": "/api/v1/company-enrich",
        "payment_required": True,
        "payment_mode": "per_request",
        "chain": "base",
        "token": "USDC",
        "amount": "0.02",
        "receiver_wallet": "0xa850773dDdAc7051c9434E3b1e804531C12d265c",
        "payment_format": "base-usdc-onchain-v1",
    }


def test_company_enrich_discovery_distinguishes_free_and_paid_tools(client):
    response = client.get("/tools")
    tools = response.json()["data"]["tools"]

    free_tool = next(item for item in tools if item["pricing_id"] == "structured_web.extract")
    paid_tool = next(item for item in tools if item["pricing_id"] == "company.enrich")

    assert free_tool["payment_required"] is False
    assert free_tool["payment_format"] is None
    assert paid_tool["payment_required"] is True
    assert paid_tool["payment_format"] == "base-usdc-onchain-v1"
