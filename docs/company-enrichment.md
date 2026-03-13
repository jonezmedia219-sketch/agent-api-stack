# Company Enrichment Guide

This guide documents the company enrichment API family and the current pricing ladder.

Base URL examples in this guide use:
- `http://localhost:8000`

For deployed integrations, replace that base URL with your public API host.

## Enrichment ladder

### 1. `POST /api/v1/company-enrich`
Cheapest single-domain homepage enrichment.

Use it when you want:
- a quick company lookup
- homepage-derived company data
- the lowest per-request cost

Pricing:
- `company.enrich`
- `0.02 USDC`

### 2. `POST /api/v1/company-enrich/deep`
Premium single-domain multi-page enrichment.

Use it when you want:
- stronger contact extraction
- better coverage from contact/about/careers/pricing pages
- richer `pages_analyzed` output

Pricing:
- `company.enrich.deep`
- `0.05 USDC`

### 3. `POST /api/v1/company-enrich/batch`
Cheaper workflow batch for homepage enrichment.

Use it when you want:
- list processing
- lower cost per domain for shallow enrichment
- per-item results without failing the entire request

Pricing:
- `company.enrich.batch`
- `0.10 USDC`
- up to 10 domains per request

### 4. `POST /api/v1/company-enrich/deep/batch`
Premium workflow batch for richer enrichment.

Use it when you want:
- deeper company research across many domains
- stronger sales/research workflows
- multi-page enrichment with per-item results

Pricing:
- `company.enrich.deep.batch`
- `0.20 USDC`
- up to 10 domains per request

## Which endpoint should I use?

- Use `company-enrich` for quick cheap single-domain lookup.
- Use `company-enrich/deep` when you need stronger emails, phones, key pages, and site signals.
- Use `company-enrich/batch` for homepage-level list processing.
- Use `company-enrich/deep/batch` for premium sales, research, and enrichment workflows.

## Agent builder guidance

For autonomous clients and agent frameworks:

- discover endpoints with `GET /tools`
- discover prices with `GET /pricing`
- discover payment format with `GET /payment/schema`
- use batch endpoints when you have multiple domains
- prefer shallow endpoints when cost matters most
- prefer deep endpoints when recall and completeness matter most

## Pricing table

| Pricing ID | Endpoint | Method | Price |
|---|---|---|---:|
| `company.enrich` | `/api/v1/company-enrich` | `POST` | `0.02 USDC` |
| `company.enrich.deep` | `/api/v1/company-enrich/deep` | `POST` | `0.05 USDC` |
| `company.enrich.batch` | `/api/v1/company-enrich/batch` | `POST` | `0.10 USDC` |
| `company.enrich.deep.batch` | `/api/v1/company-enrich/deep/batch` | `POST` | `0.20 USDC` |

## Example: shallow single-domain request

```bash
curl -X POST http://localhost:8000/api/v1/company-enrich \
  -H "Content-Type: application/json" \
  -H "X-Payment-Format: base-usdc-onchain-v1" \
  -H "X-Payment-Proof: <base64url-encoded-json>" \
  -d '{"domain":"example.com"}'
```

Example response:

```json
{
  "ok": true,
  "data": {
    "domain": "example.com",
    "normalized_url": "https://example.com/",
    "company_name": "Example Inc",
    "summary": "Example Inc helps revenue teams automate outbound and enrich company data.",
    "industry": "saas",
    "emails": ["hello@example.com"],
    "phone_numbers": ["+1 (555) 123-4567"],
    "social_links": ["https://www.linkedin.com/company/exampleinc"],
    "contact_page": "https://example.com/contact",
    "about_page": "https://example.com/about",
    "careers_page": "https://example.com/careers",
    "pricing_page": "https://example.com/pricing",
    "important_links": [
      "https://example.com/contact",
      "https://example.com/about",
      "https://example.com/careers",
      "https://example.com/pricing"
    ],
    "addresses": ["123 Main Street, Austin, TX 78701"],
    "signals": {
      "has_contact_page": true,
      "has_about_page": true,
      "has_careers_page": true,
      "has_pricing_page": true,
      "has_api_docs": false,
      "has_blog": false,
      "has_login": false,
      "has_signup": false
    },
    "pages_analyzed": ["https://example.com/"]
  }
}
```

## Example: deep single-domain request

```bash
curl -X POST http://localhost:8000/api/v1/company-enrich/deep \
  -H "Content-Type: application/json" \
  -H "X-Payment-Format: base-usdc-onchain-v1" \
  -H "X-Payment-Proof: <base64url-encoded-json>" \
  -d '{"domain":"example.com"}'
```

Example response:

```json
{
  "ok": true,
  "data": {
    "domain": "example.com",
    "normalized_url": "https://example.com/",
    "company_name": "Example Inc",
    "summary": "Example Inc helps revenue teams automate outbound and enrich company data.",
    "industry": "saas",
    "emails": ["hello@example.com", "sales@example.com"],
    "phone_numbers": ["+1 (555) 123-4567"],
    "social_links": ["https://www.linkedin.com/company/exampleinc"],
    "contact_page": "https://example.com/contact",
    "about_page": "https://example.com/about",
    "careers_page": "https://example.com/careers",
    "pricing_page": "https://example.com/pricing",
    "important_links": [
      "https://example.com/contact",
      "https://example.com/about",
      "https://example.com/careers",
      "https://example.com/pricing"
    ],
    "addresses": ["123 Main Street, Austin, TX 78701"],
    "signals": {
      "has_contact_page": true,
      "has_about_page": true,
      "has_careers_page": true,
      "has_pricing_page": true,
      "has_api_docs": true,
      "has_blog": false,
      "has_login": false,
      "has_signup": false
    },
    "pages_analyzed": [
      "https://example.com/",
      "https://example.com/contact",
      "https://example.com/about",
      "https://example.com/careers",
      "https://example.com/pricing"
    ]
  }
}
```

## Example: shallow batch request

```bash
curl -X POST http://localhost:8000/api/v1/company-enrich/batch \
  -H "Content-Type: application/json" \
  -H "X-Payment-Format: base-usdc-onchain-v1" \
  -H "X-Payment-Proof: <base64url-encoded-json>" \
  -d '{"domains":["example.com","acme.co","bad domain"]}'
```

Example response:

```json
{
  "ok": true,
  "data": {
    "results": [
      {
        "domain": "example.com",
        "ok": true,
        "data": {
          "domain": "example.com",
          "normalized_url": "https://example.com/",
          "company_name": "Example Inc",
          "summary": "Example Inc helps revenue teams automate outbound and enrich company data.",
          "industry": "saas",
          "emails": ["hello@example.com"],
          "phone_numbers": ["+1 (555) 123-4567"],
          "social_links": ["https://www.linkedin.com/company/exampleinc"],
          "contact_page": "https://example.com/contact",
          "about_page": "https://example.com/about",
          "careers_page": "https://example.com/careers",
          "pricing_page": "https://example.com/pricing",
          "important_links": [],
          "addresses": [],
          "signals": {
            "has_contact_page": true,
            "has_about_page": true,
            "has_careers_page": true,
            "has_pricing_page": true,
            "has_api_docs": false,
            "has_blog": false,
            "has_login": false,
            "has_signup": false
          },
          "pages_analyzed": ["https://example.com/"]
        }
      },
      {
        "domain": "bad domain",
        "ok": false,
        "error": {
          "code": "INVALID_INPUT",
          "message": "A valid domain is required.",
          "retryable": false
        }
      }
    ],
    "count": 2,
    "success_count": 1,
    "error_count": 1
  }
}
```

## Example: deep batch request

```bash
curl -X POST http://localhost:8000/api/v1/company-enrich/deep/batch \
  -H "Content-Type: application/json" \
  -H "X-Payment-Format: base-usdc-onchain-v1" \
  -H "X-Payment-Proof: <base64url-encoded-json>" \
  -d '{"domains":["example.com","acme.co","bad domain"]}'
```

Example response:

```json
{
  "ok": true,
  "data": {
    "results": [
      {
        "domain": "example.com",
        "ok": true,
        "data": {
          "domain": "example.com",
          "normalized_url": "https://example.com/",
          "company_name": "Example Inc",
          "summary": "Example Inc helps revenue teams automate outbound and enrich company data.",
          "industry": "saas",
          "emails": ["hello@example.com", "sales@example.com"],
          "phone_numbers": ["+1 (555) 123-4567"],
          "social_links": [],
          "contact_page": "https://example.com/contact",
          "about_page": "https://example.com/about",
          "careers_page": "https://example.com/careers",
          "pricing_page": "https://example.com/pricing",
          "important_links": [],
          "addresses": [],
          "signals": {
            "has_contact_page": true,
            "has_about_page": true,
            "has_careers_page": true,
            "has_pricing_page": true,
            "has_api_docs": true,
            "has_blog": false,
            "has_login": false,
            "has_signup": false
          },
          "pages_analyzed": [
            "https://example.com/",
            "https://example.com/contact",
            "https://example.com/about",
            "https://example.com/careers",
            "https://example.com/pricing"
          ]
        }
      },
      {
        "domain": "bad domain",
        "ok": false,
        "error": {
          "code": "INVALID_INPUT",
          "message": "A valid domain is required.",
          "retryable": false
        }
      }
    ],
    "count": 2,
    "success_count": 1,
    "error_count": 1
  }
}
```