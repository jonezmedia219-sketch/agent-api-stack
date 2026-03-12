# Agent-api-stack

Agent-ready API stack with free tools, paid lead extraction, onchain Base USDC verification, and machine-readable pricing/payment discovery.

Live API: https://agent-api-stack.onrender.com/docs

## Try it now

- Service discovery: GET /
- Interactive docs: /docs
- Pricing discovery: /pricing
- Payment schema: /payment/schema

Free endpoints:
- GET /api/v1/search
- POST /api/v1/structured-web/extract
- POST /api/v1/structured-web/extract-html

Paid endpoint:
- POST /api/v1/lead-extract


This repo now implements:

- API #1: **Structured Web Data API**
- API #2: **Contact / Lead Extraction API**
- API #3: **Search Aggregation API**

It also includes a shared monetization-ready billing abstraction for:
- pricing identifiers
- usage recording
- request usage context
- payment verification hooks
- payment policy + enforcement scaffolding

## API endpoints

- `GET /health`
- `POST /api/v1/structured-web/extract`
- `POST /api/v1/structured-web/extract-html`
- `POST /api/v1/lead-extract`
- `GET /api/v1/search`
- `GET /docs`
- `GET /pricing`
- `GET /payment/schema`

## Developer docs and discovery

- Interactive API docs: `/docs`
- Pricing discovery: `/pricing`
- Payment schema discovery: `/payment/schema`
- Integration guide: `docs/integration-payments.md`

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
│  │  └─ v1/structured_web.py
│  ├─ core/
│  │  ├─ http_client.py
│  │  ├─ html_utils.py
│  │  ├─ metadata_utils.py
│  │  ├─ response_builders.py
│  │  ├─ text_utils.py
│  │  ├─ url_utils.py
│  │  └─ validators.py
│  ├─ middleware/
│  │  ├─ access_log.py
│  │  ├─ metering.py
│  │  ├─ payment_stub.py
│  │  └─ request_id.py
│  ├─ models/
│  │  ├─ common.py
│  │  └─ structured_web.py
│  ├─ services/
│  │  └─ structured_web/
│  │     ├─ cleaner.py
│  │     ├─ detectors.py
│  │     ├─ extractor.py
│  │     └─ service.py
│  └─ billing/
│     ├─ metering.py
│     ├─ models.py
│     ├─ payment_hooks.py
│     └─ pricing.py
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
- `GET /api/v1/search`
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
