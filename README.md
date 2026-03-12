# Agent API Stack

A small, modular FastAPI monorepo for agent-friendly infrastructure APIs.

This repo now implements:

- API #1: **Structured Web Data API**
- API #2: **Contact / Lead Extraction API**
- API #3: **Search Aggregation API**

It also includes a shared monetization-ready billing abstraction for:
- pricing identifiers
- usage recording
- request usage context
- payment verification hooks

## API endpoints

- `GET /health`
- `POST /api/v1/structured-web/extract`
- `POST /api/v1/structured-web/extract-html`
- `POST /api/v1/lead-extract`
- `GET /api/v1/search`
- `GET /docs`

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

Endpoint handlers no longer emit raw usage events directly. They build a lightweight request usage context and call a single shared helper:

```python
record_usage("search.query", usage_context)
```

That keeps endpoint code clean while preserving a clean seam for x402 or another per-request payment layer later.
