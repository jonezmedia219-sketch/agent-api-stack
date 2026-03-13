# Agent-api-stack

Agent-ready API stack with free tools, paid lead extraction, paid company enrichment, onchain Base USDC verification, and machine-readable pricing/payment discovery.

Live API: https://agent-api-stack.onrender.com/docs

## Try it now

- Service discovery: `GET /`
- Interactive docs: `/docs`
- Pricing discovery: `/pricing`
- Payment schema: `/payment/schema`
- Tool discovery: `/tools`

Free endpoints:
- `GET /api/v1/search`
- `POST /api/v1/structured-web/extract`
- `POST /api/v1/structured-web/extract-html`

Paid endpoints:
- `POST /api/v1/lead-extract`
- `POST /api/v1/company-enrich`
- `POST /api/v1/company-enrich/deep`
- `POST /api/v1/company-enrich/batch`
- `POST /api/v1/company-enrich/deep/batch`

This repo now implements:

- API #1: **Structured Web Data API**
- API #2: **Contact / Lead Extraction API**
- API #3: **Search Aggregation API**
- API #4: **Company Enrichment API Family**

It also includes a shared monetization-ready billing abstraction for:
- pricing identifiers
- usage recording
- request usage context
- payment verification hooks
- payment policy + enforcement scaffolding

## API endpoints

- `GET /health`
- `GET /api/v1/search`
- `POST /api/v1/structured-web/extract`
- `POST /api/v1/structured-web/extract-html`
- `POST /api/v1/lead-extract`
- `POST /api/v1/company-enrich`
- `POST /api/v1/company-enrich/deep`
- `POST /api/v1/company-enrich/batch`
- `POST /api/v1/company-enrich/deep/batch`
- `GET /tools`
- `GET /docs`
- `GET /pricing`
- `GET /payment/schema`

## Developer docs and discovery

- Interactive API docs: `/docs`
- Tool discovery: `/tools`
- Pricing discovery: `/pricing`
- Payment schema discovery: `/payment/schema`
- Integration guide: `docs/integration-payments.md`
- Company enrichment guide: `docs/company-enrichment.md`

## Company enrichment ladder

### `POST /api/v1/company-enrich`
Cheapest single-domain homepage enrichment.

Use it for:
- quick cheap single-domain lookup
- homepage-derived company data
- lowest-cost enrichment

Pricing:
- `company.enrich`
- `0.02 USDC`

### `POST /api/v1/company-enrich/deep`
Premium single-domain multi-page enrichment.

Use it for:
- stronger emails, phone numbers, and page detection
- richer site signals
- multi-page `pages_analyzed`

Pricing:
- `company.enrich.deep`
- `0.05 USDC`

### `POST /api/v1/company-enrich/batch`
Cheaper workflow batch for homepage enrichment.

Use it for:
- list processing
- workflow batching
- per-item results without failing the full request

Pricing:
- `company.enrich.batch`
- `0.10 USDC`
- up to 10 domains per request

### `POST /api/v1/company-enrich/deep/batch`
Premium workflow batch for richer enrichment.

Use it for:
- premium sales/research workflows
- deeper multi-domain enrichment
- stronger recall/completeness across multiple domains

Pricing:
- `company.enrich.deep.batch`
- `0.20 USDC`
- up to 10 domains per request

## Which endpoint should I use?

- Use `company-enrich` for quick cheap single-domain lookup.
- Use `company-enrich/deep` when you need stronger emails, phones, key pages, and signals.
- Use `company-enrich/batch` for homepage-level list processing.
- Use `company-enrich/deep/batch` for premium sales and research workflows.

## Pricing table

| Pricing ID | Endpoint | Method | Price |
|---|---|---|---:|
| `company.enrich` | `/api/v1/company-enrich` | `POST` | `0.02 USDC` |
| `company.enrich.deep` | `/api/v1/company-enrich/deep` | `POST` | `0.05 USDC` |
| `company.enrich.batch` | `/api/v1/company-enrich/batch` | `POST` | `0.10 USDC` |
| `company.enrich.deep.batch` | `/api/v1/company-enrich/deep/batch` | `POST` | `0.20 USDC` |

## Agent-oriented guidance

For autonomous clients and agent builders:

- discover endpoints with `GET /tools`
- discover prices with `GET /pricing`
- discover payment format with `GET /payment/schema`
- use batch endpoints for multiple domains
- prefer shallow endpoints when cost matters most
- prefer deep endpoints when recall and completeness matter most

## What the Structured Web Data API returns

Given a URL or raw HTML, the structured web API extracts:

- `title`
- `author`
- `published_date`
- `summary`
- `main_text`
- `headings`
- `links`
- `metadata`
- `content_type`

## What the Contact / Lead Extraction API returns

Given a URL or raw HTML, the lead extraction API extracts:

- `emails`
- `phone_numbers`
- `social_media_links`
- `company_name`
- `contact_forms_detected`
- `addresses`

## What the Company Enrichment API returns

The company enrichment endpoints return company-level structured data such as:

- `domain`
- `normalized_url`
- `company_name`
- `summary`
- `industry`
- `emails`
- `phone_numbers`
- `social_links`
- `contact_page`
- `about_page`
- `careers_page`
- `pricing_page`
- `important_links`
- `addresses`
- `signals.has_careers_page`
- `pages_analyzed`

## What the Search Aggregation API returns

Given a query string, the search API returns normalized results containing:

- `title`
- `url`
- `snippet`
- `source`
- `rank`

## Why these dependencies

- **FastAPI**: clean REST API framework with strong validation and docs.
- **httpx**: async HTTP client for fetching webpages.
- **beautifulsoup4 + lxml**: dependable HTML parsing.
- **readability-lxml**: useful boilerplate reduction for articles and content-heavy pages.
- **python-dateutil**: resilient published-date parsing.
- **pydantic / pydantic-settings**: request validation and env-based config.
- **pytest**: straightforward test coverage for API and extraction behavior.

## Project structure

```text
agent-api-stack/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ logging.py
│  ├─ exceptions.py
│  ├─ api/
│  │  ├─ health.py
│  │  └─ v1/
│  ├─ core/
│  ├─ middleware/
│  ├─ models/
│  ├─ services/
│  └─ billing/
├─ docs/
├─ tests/
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
└─ .env.example
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker setup

```bash
docker build -t agent-api-stack .
docker run --rm -p 8000:8000 --env-file .env agent-api-stack
```

The container runs FastAPI with:
- port `8000`
- `uvicorn app.main:app`
- proxy header support enabled for reverse proxies / public hosts

## Example requests

### Extract from URL

```bash
curl -X POST http://localhost:8000/api/v1/structured-web/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/blog/post"}'
```

### Extract from raw HTML

```bash
curl -X POST http://localhost:8000/api/v1/structured-web/extract-html \
  -H "Content-Type: application/json" \
  -d '{"html": "<html><body><article><h1>Hello</h1><p>World</p></article></body></html>", "source_url": "https://example.com"}'
```

### Lead extract from URL

```bash
curl -X POST http://localhost:8000/api/v1/lead-extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://acmegrowth.com/contact"}'
```

### Lead extract from raw HTML

```bash
curl -X POST http://localhost:8000/api/v1/lead-extract \
  -H "Content-Type: application/json" \
  -d '{"html": "<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>", "source_url": "https://acme.com"}'
```

### Company enrich

```bash
curl -X POST http://localhost:8000/api/v1/company-enrich \
  -H "Content-Type: application/json" \
  -H "X-Payment-Format: base-usdc-onchain-v1" \
  -H "X-Payment-Proof: <base64url-encoded-json>" \
  -d '{"domain": "example.com"}'
```

### Company enrich deep

```bash
curl -X POST http://localhost:8000/api/v1/company-enrich/deep \
  -H "Content-Type: application/json" \
  -H "X-Payment-Format: base-usdc-onchain-v1" \
  -H "X-Payment-Proof: <base64url-encoded-json>" \
  -d '{"domain": "example.com"}'
```

### Company enrich batch

```bash
curl -X POST http://localhost:8000/api/v1/company-enrich/batch \
  -H "Content-Type: application/json" \
  -H "X-Payment-Format: base-usdc-onchain-v1" \
  -H "X-Payment-Proof: <base64url-encoded-json>" \
  -d '{"domains": ["example.com", "acme.co", "stripe.com"]}'
```

### Company enrich deep batch

```bash
curl -X POST http://localhost:8000/api/v1/company-enrich/deep/batch \
  -H "Content-Type: application/json" \
  -H "X-Payment-Format: base-usdc-onchain-v1" \
  -H "X-Payment-Proof: <base64url-encoded-json>" \
  -d '{"domains": ["example.com", "acme.co", "stripe.com"]}'
```

### Search query

```bash
curl "http://localhost:8000/api/v1/search?q=agent%20infrastructure&limit=3&source=mock"
```

## Running tests

```bash
pytest
```

## Deployment

A full public deployment runbook is available in `DEPLOYMENT.md`.

Quick summary:

### Local development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker / container host

```bash
docker build -t agent-api-stack .
docker run --rm -p 8000:8000 --env-file .env agent-api-stack
```

### Recommended first public host

- **Render** for fastest stable launch
- **Fly.io** second
- **VPS + Docker + Caddy** third for first launch, but strongest for long-term control

### External agent base URL pattern

```text
https://api.yourdomain.com
```

Agents call:

- `POST /api/v1/structured-web/extract`
- `POST /api/v1/structured-web/extract-html`
- `POST /api/v1/lead-extract`
- `POST /api/v1/company-enrich`
- `POST /api/v1/company-enrich/deep`
- `POST /api/v1/company-enrich/batch`
- `POST /api/v1/company-enrich/deep/batch`
- `GET /api/v1/search`
- `GET /tools`
- `GET /pricing`
- `GET /payment/schema`
- `GET /docs`

## Safety guards

This stack now includes lightweight deployment guards:

- request body size limit via `REQUEST_MAX_BODY_BYTES`
- per-client rate limiting via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`
- outbound fetch size limiting via `HTTP_MAX_RESPONSE_BYTES`
- HTML input size limiting via `STRUCTURED_WEB_MAX_HTML_CHARS`
- CORS disabled by default unless `CORS_ALLOW_ORIGINS` is explicitly set

## Notes on monetization readiness

This repo now includes a shared billing abstraction layer for:

- pricing identifier lookup
- usage record creation
- request usage context
- structured usage event emission
- payment verification hooks
- payment policy registry
- payment enforcement helper
- stub verifier for safe rollout

Endpoint handlers no longer emit raw usage events directly. They build a lightweight request usage context and call a single shared helper for metering:

```python
record_usage("search.query", usage_context)
```

Payment enforcement is kept outside endpoint business logic through a shared helper:

```python
await enforce_payment(request, endpoint="lead_extract.url")
```

Current rollout mode is safe by default:
- free endpoints always pass
- paid-capable endpoints can run in shadow mode first
- hard enforcement can be enabled later for selected endpoints
- structured HTTP 402 responses are ready for unpaid paid requests
- verifier can be switched between `stub` and `x402`

For paid requests, verifier mode can now be one of:
- `stub`
- `x402`
- `base_usdc_onchain`

Exact onchain verifier request headers:
- `X-Payment-Format: base-usdc-onchain-v1`
- `X-Payment-Proof: <base64url-encoded-json>`

Exact x402-style signed-proof headers:
- `X-Payment-Format: x402-base-usdc-v1`
- `X-Payment-Proof: <base64url-encoded-json>`

Backward compatibility currently accepted:
- `X-Payment-Prof` is temporarily accepted in code
- canonical public header name is `X-Payment-Proof`

Exact onchain verifier env vars:
- `PAYMENT_VERIFIER=base_usdc_onchain`
- `PAYMENT_RECEIVER_WALLET=0xa850773dDdAc7051c9434E3b1e804531C12d265c`
- `BASE_RPC_URL=https://mainnet.base.org`
- `PAYMENT_TOKEN_CONTRACT=0x833589fCD6EDB6E08f4c7C32D4f71b54bdA02913`
- `PAYMENT_MIN_CONFIRMATIONS=1`

Backward compatibility currently accepted:
- `PAYMENT_RECEIVER_WALET` is temporarily accepted in config
- canonical env var name is `PAYMENT_RECEIVER_WALLET`

This preserves a clean seam for real onchain verification, x402-compatible attestation flows, or prepaid credits later.
