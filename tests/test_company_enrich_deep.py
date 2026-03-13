from unittest.mock import AsyncMock, patch


HOMEPAGE_HTML = """
<html>
  <head>
    <title>Example Inc | SaaS Growth Platform</title>
    <meta name='description' content='Example Inc helps revenue teams automate outbound and enrich company data.' />
    <meta property='og:site_name' content='Example Inc' />
  </head>
  <body>
    <a href='/about'>About</a>
    <a href='/contact'>Contact</a>
    <a href='/careers'>Careers</a>
    <a href='/pricing'>Pricing</a>
    <a href='/developers'>API Docs</a>
    <a href='/blog'>Blog</a>
    <a href='/login'>Login</a>
    <a href='/signup'>Sign Up</a>
    <p>Email hello@example.com</p>
    <p>Call +1 (555) 123-4567</p>
    <p>HQ: 123 Main Street, Austin, TX 78701</p>
  </body>
</html>
"""

CONTACT_HTML = """
<html><body>
  <h1>Contact</h1>
  <p>Email sales@example.com and hello@example.com</p>
  <p>Call +1 (555) 123-4567 or +1 (555) 888-9999</p>
  <p>123 Main Street, Austin, TX 78701</p>
</body></html>
"""

ABOUT_HTML = """
<html><body>
  <h1>About Example Inc</h1>
  <p>Example Inc builds workflow automation software for modern sales teams.</p>
  <a href='https://www.linkedin.com/company/exampleinc'>LinkedIn</a>
</body></html>
"""

CAREERS_HTML = """
<html><body>
  <h1>Careers</h1>
  <p>We're hiring growth engineers.</p>
</body></html>
"""

PRICING_HTML = """
<html><body>
  <h1>Pricing</h1>
  <p>Plans for startups and enterprise.</p>
</body></html>
"""


def _fetch_side_effect(url: str):
    mapping = {
        "https://example.com/": (HOMEPAGE_HTML, "text/html", "https://example.com/"),
        "https://example.com/contact": (CONTACT_HTML, "text/html", "https://example.com/contact"),
        "https://example.com/about": (ABOUT_HTML, "text/html", "https://example.com/about"),
        "https://example.com/careers": (CAREERS_HTML, "text/html", "https://example.com/careers"),
        "https://example.com/pricing": (PRICING_HTML, "text/html", "https://example.com/pricing"),
        "https://solo.com/": ("<html><body><h1>Solo Co</h1><p>Email hi@solo.com</p></body></html>", "text/html", "https://solo.com/"),
    }
    return mapping[url]


def test_company_enrich_deep_returns_200_for_mocked_homepage_and_subpages(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(side_effect=_fetch_side_effect)):
        response = client.post("/api/v1/company-enrich/deep", json={"domain": "example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["domain"] == "example.com"
    assert data["normalized_url"] == "https://example.com/"
    assert data["contact_page"] == "https://example.com/contact"
    assert data["about_page"] == "https://example.com/about"
    assert data["careers_page"] == "https://example.com/careers"
    assert data["pricing_page"] == "https://example.com/pricing"
    assert data["signals"]["has_api_docs"] is True
    assert data["signals"]["has_blog"] is True
    assert data["signals"]["has_login"] is True
    assert data["signals"]["has_signup"] is True
    assert data["pages_analyzed"] == [
        "https://example.com/",
        "https://example.com/contact",
        "https://example.com/about",
        "https://example.com/careers",
        "https://example.com/pricing",
    ]


def test_company_enrich_deep_deduplicates_merged_fields(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(side_effect=_fetch_side_effect)):
        response = client.post("/api/v1/company-enrich/deep", json={"domain": "example.com"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["emails"] == ["hello@example.com", "sales@example.com"]
    assert data["phone_numbers"] == ["+1 (555) 123-4567", "+1 (555) 888-9999"]
    assert data["addresses"] == ["123 Main Street, Austin, TX 78701"]


def test_company_enrich_deep_succeeds_when_no_extra_pages_found(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(side_effect=_fetch_side_effect)):
        response = client.post("/api/v1/company-enrich/deep", json={"domain": "solo.com"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["domain"] == "solo.com"
    assert data["emails"] == ["hi@solo.com"]
    assert data["pages_analyzed"] == ["https://solo.com/"]


def test_company_enrich_deep_invalid_domain_returns_invalid_input(client):
    response = client.post("/api/v1/company-enrich/deep", json={"domain": "bad domain"})

    assert response.status_code == 400
    assert response.json() == {
        "ok": False,
        "error": {
            "code": "INVALID_INPUT",
            "message": "A valid domain is required.",
            "retryable": False,
        },
    }


def test_company_enrich_deep_route_path_and_schema_names_are_correct(client):
    with patch("app.services.company_enrich.service.fetch_page", new=AsyncMock(side_effect=_fetch_side_effect)):
        response = client.post("/api/v1/company-enrich/deep", json={"domain": "example.com"})

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
    assert data["careers_page"] == "https://example.com/careers"
    assert data["signals"]["has_careers_page"] is True


def test_company_enrich_deep_endpoint_is_listed_in_tools(client):
    response = client.get("/tools")
    assert response.status_code == 200
    tools = response.json()["data"]["tools"]
    entry = next(item for item in tools if item["pricing_id"] == "company.enrich.deep")
    assert entry["endpoint"] == "/api/v1/company-enrich/deep"
    assert entry["method"] == "POST"
    assert entry["payment_required"] is True
    assert entry["payment_format"] == "base-usdc-onchain-v1"
    assert entry["expected_inputs"] == {"json_body": {"domain": "string"}}


def test_company_enrich_deep_pricing_metadata_exists(client):
    response = client.get("/pricing")
    assert response.status_code == 200
    endpoints = response.json()["data"]["endpoints"]
    entry = next(item for item in endpoints if item["pricing_id"] == "company.enrich.deep")
    assert entry == {
        "pricing_id": "company.enrich.deep",
        "method": "POST",
        "path": "/api/v1/company-enrich/deep",
        "payment_required": True,
        "payment_mode": "per_request",
        "chain": "base",
        "token": "USDC",
        "amount": "0.05",
        "receiver_wallet": "0xa850773dDdAc7051c9434E3b1e804531C12d265c",
        "payment_format": "base-usdc-onchain-v1",
    }


def test_company_enrich_deep_discovery_is_paid(client):
    response = client.get("/tools")
    tools = response.json()["data"]["tools"]
    deep_tool = next(item for item in tools if item["pricing_id"] == "company.enrich.deep")
    assert deep_tool["payment_required"] is True
    assert deep_tool["payment_format"] == "base-usdc-onchain-v1"
