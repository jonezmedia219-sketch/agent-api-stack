# Public Deployment Runbook

This project is a containerized FastAPI API stack designed to run as a public web service for external agents.

## Recommended host ranking

### 1. Render
**Why it ranks first**
- Very fast path from repo to public HTTPS URL
- Native Dockerfile deployment
- Reliable enough for an MVP public API
- Built-in TLS and health checks
- Minimal ops burden

**Trade-offs**
- Less infrastructure control than a VPS
- Ongoing cost can exceed a bare VPS over time

### 2. Fly.io
**Why it ranks second**
- Great fit for Dockerized APIs
- Strong production feel for public services
- Good regional deployment story
- Built-in HTTPS

**Trade-offs**
- Slightly more setup friction than Render
- More platform-specific operational concepts

### 3. VPS + Docker + Caddy
**Why it ranks third for first launch**
- Best long-term control
- Excellent for future payment/proxy customization
- Lowest platform lock-in

**Trade-offs**
- More setup time
- You manage patches, TLS, proxying, restarts, and firewall rules

## Chosen first deployment option

**Render** is the best first launch environment.

Why:
- fastest route to a stable public API
- Docker-compatible with almost no extra infrastructure
- HTTPS and public URL are handled for you
- easy to connect a custom domain later
- low operational overhead while validating demand

## Important port note

The application listens internally on port `8000`.

On Render and similar platforms, the public service does not need to expose external port `8000` directly. The platform routes public HTTPS traffic to the container automatically.

If you deploy on your own VPS later, you can publish port `8000` behind a reverse proxy, or map external `80/443` to the container.

## Repo files used for deployment

- `Dockerfile`
- `.env.example`
- `render.yaml`
- `README.md`

## Environment variables

Minimum useful production variables:

- `APP_ENV=production`
- `APP_HOST=0.0.0.0`
- `APP_PORT=8000`
- `LOG_LEVEL=INFO`
- `HTTP_TIMEOUT_SECONDS=15`
- `HTTP_MAX_RESPONSE_BYTES=2000000`
- `STRUCTURED_WEB_MAX_HTML_CHARS=500000`
- `STRUCTURED_WEB_MAX_LINKS=100`
- `REQUEST_MAX_BODY_BYTES=1000000`
- `RATE_LIMIT_REQUESTS=60`
- `RATE_LIMIT_WINDOW_SECONDS=60`
- `ENABLE_METERING=true`
- `ENABLE_PAYMENT_ENFORCEMENT=false`

Optional:
- `CORS_ALLOW_ORIGINS=https://agent.example.com,https://app.example.com`

Onchain payment verifier variables (do not enable until ready):
- `PAYMENT_VERIFIER=base_usdc_onchain`
- `PAYMENT_RECEIVER_WALLET=0xa850773dDdAc7051c9434E3b1e804531C12d265c`
- `BASE_RPC_URL=https://mainnet.base.org`
- `PAYMENT_TOKEN_CONTRACT=0x833589fCD6EDB6E08f4c7C32D4f71b54bdA02913`
- `PAYMENT_MIN_CONFIRMATIONS=1`

Backward compatibility currently accepted:
- request header alias: `X-Payment-Prof`
- env var alias: `PAYMENT_RECEIVER_WALET`

Canonical names for production use:
- `X-Payment-Proof`
- `PAYMENT_RECEIVER_WALLET`

## Render deployment steps

### Option A: Deploy directly from GitHub repo
1. Push this repo to GitHub.
2. Sign in to Render.
3. Click **New +** → **Blueprint**.
4. Connect the GitHub repo.
5. Render will detect `render.yaml`.
6. Review the generated web service settings.
7. Create the service.
8. Wait for the image build and deploy to finish.
9. Open the generated Render URL.

### Option B: Deploy from a Docker image
1. Build the image locally:
   ```bash
   docker build -t agent-api-stack .
   ```
2. Tag and push it to a container registry if needed.
3. Create a Render web service using that image.
4. Set environment variables from the list above.
5. Deploy and wait for health checks to pass.

## Local validation before deployment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pytest
```

## Post-deploy launch verification checklist

Assume your public base URL is:

```text
https://api.yourdomain.com
```

### 1. Health
```bash
curl https://api.yourdomain.com/health
```
Expected:
- HTTP 200
- `{ "ok": true, "status": "healthy" }`

### 2. Docs
Open:
```text
https://api.yourdomain.com/docs
```
Expected:
- Swagger UI loads

### 3. Structured web extraction
```bash
curl -X POST https://api.yourdomain.com/api/v1/structured-web/extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```
Expected:
- HTTP 200
- `ok: true`
- structured article/page JSON under `data`

### 4. Lead extract
```bash
curl -X POST https://api.yourdomain.com/api/v1/lead-extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/contact"}'
```
Expected:
- HTTP 200
- `ok: true`
- lead/contact fields under `data`

### 5. Search
```bash
curl "https://api.yourdomain.com/api/v1/search?q=agent%20infrastructure&limit=3&source=mock"
```
Expected:
- HTTP 200
- normalized search results under `data.results`

## Custom domain + HTTPS

### Render-managed domain
- Render gives you a default public HTTPS URL automatically.

### Custom domain / subdomain
1. In Render, open the service settings.
2. Add a custom domain such as:
   - `api.yourdomain.com`
3. Create the DNS record Render requests.
4. Wait for DNS verification.
5. Render provisions HTTPS automatically.

## External agent usage examples

### Structured Web API
```bash
curl -X POST https://api.yourdomain.com/api/v1/structured-web/extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/blog/post"}'
```

### Lead Extraction API
```bash
curl -X POST https://api.yourdomain.com/api/v1/lead-extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/contact"}'
```

### Lead Extraction API with real onchain payment headers
```bash
curl -X POST https://api.yourdomain.com/api/v1/lead-extract \
  -H "Content-Type: application/json" \
  -H "X-Payment-Format: base-usdc-onchain-v1" \
  -H "X-Payment-Proof: <base64url-encoded-json>" \
  -d '{"html":"<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>","source_url":"https://acme.com"}'
```

### Search API
```bash
curl "https://api.yourdomain.com/api/v1/search?q=lead%20gen%20tools&limit=5&source=mock"
```

## Future move to a VPS

Once traffic or monetization justifies more control, move the same container to:
- VPS + Docker Compose
- Caddy or Nginx reverse proxy
- your own domain + TLS

The current repo structure is already compatible with that transition.
