# Integration Guide: Payments and Discovery

This guide is for external developers and agent clients integrating with the API's free and paid endpoints.

Canonical example base URL in this guide:
- `https://YOUR_API_BASE_URL`

Current live deployment may differ. If you have a deployed host, substitute that base URL in the examples below.

## 1. API overview

This API exposes both free and paid endpoints.

**Free endpoints**
- `GET /api/v1/search`
- `POST /api/v1/structured-web/extract`
- `POST /api/v1/structured-web/extract-html`

**Paid endpoint**
- `POST /api/v1/lead-extract`

For `POST /api/v1/lead-extract`, the pricing identifier depends on request mode:
- HTML body mode → `lead_extract.html`
- URL mode → `lead_extract.url`

Free endpoints do not require payment.

## 2. Free vs paid endpoints

### Free endpoints

#### `GET /api/v1/search`
Search aggregation endpoint.

#### `POST /api/v1/structured-web/extract`
Structured extraction from a URL.

#### `POST /api/v1/structured-web/extract-html`
Structured extraction from raw HTML.

### Paid endpoint

#### `POST /api/v1/lead-extract`
Lead/contact extraction from either:
- raw HTML
- a URL

## 3. Pricing discovery

Use:
- `GET /pricing`

This endpoint is public and machine-readable. It tells clients:
- which endpoints are free vs paid
- which pricing ID to use
- which method/path to call
- chain/token/amount/receiver wallet for paid routes
- canonical payment format

### curl

```bash
curl "https://YOUR_API_BASE_URL/pricing"
```

### PowerShell

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "https://YOUR_API_BASE_URL/pricing"
```

## 4. Payment schema discovery

Use:
- `GET /payment/schema`

This endpoint is public and machine-readable. It tells clients:
- the canonical production payment format
- the canonical public headers
- the signed message format
- required proof fields
- replay-protection fields

### Canonical production format
- `base-usdc-onchain-v1`

### Canonical public headers
- `X-Payment-Format`
- `X-Payment-Proof`

### curl

```bash
curl "https://YOUR_API_BASE_URL/payment/schema"
```

### PowerShell

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "https://YOUR_API_BASE_URL/payment/schema"
```

## 5. Canonical payment headers

For paid requests, send these headers:

- `X-Payment-Format: base-usdc-onchain-v1`
- `X-Payment-Proof: <base64url-encoded-json>`

Use the canonical public headers above in client integrations.

## 6. Exact proof flow

### Step 1: discover pricing
Call `GET /pricing` and find the entry for the endpoint you want to call.

### Step 2: construct request body
Create the exact JSON body you will send to the paid endpoint.

### Step 3: hash request body
Hash the exact request body bytes with SHA-256.

The proof must be bound to the exact body you submit.

### Step 4: send onchain Base USDC payment
Send the required payment on Base using the pricing details from `/pricing`.

### Step 5: get tx hash
Capture the final transaction hash from the confirmed payment transaction.

### Step 6: sign canonical message
Sign the canonical pipe-delimited message used by the verifier.

### Step 7: assemble proof
Build the proof JSON object, then base64url-encode it into the `X-Payment-Proof` header value.

### Step 8: send API request
Send the paid API request with:
- the exact same method
- the exact same path
- the exact same request body
- `X-Payment-Format`
- `X-Payment-Proof`

## 7. Canonical signed message format

The onchain verifier signs this exact pipe-delimited message shape:

```text
version|chain_id|pricing_id|payment_mode|receiver_wallet|token_contract|request_binding.method|request_binding.path|request_binding.body_sha256|quote_id|nonce|timestamp|amount|tx_hash
```

Example shape:

```text
base-usdc-onchain-v1|8453|lead_extract.html|per_request|0xa850773dDdAc7051c9434E3b1e804531C12d265c|0x833589fCD6EDB6E08f4c7C32D4f71b54bdA02913|POST|/api/v1/lead-extract|<body_sha256>|<quote_id>|<nonce>|<timestamp>|0.01|<tx_hash>
```

## 8. Replay warning

Proofs must be fresh.

Do not reuse the same:
- `tx_hash`
- `nonce`
- `quote_id`

If you replay a proof, the server should reject it.

## 9. Common 402 reasons

Payment failures return:
- HTTP `402`
- `error.code = PAYMENT_REQUIRED`
- machine-friendly `error.details.reason`

Common reasons include:

- `missing_or_invalid_payment_headers` — required payment headers are missing or invalid
- `malformed_payment_proof` — proof could not be decoded or parsed
- `invalid_chain_id` — proof was built for the wrong chain
- `invalid_pricing_id` — pricing ID does not match the request
- `invalid_request_binding` — method/path binding does not match the request
- `invalid_request_body_binding` — body hash does not match the submitted body
- `invalid_receiver_wallet` — proof receiver wallet does not match server config
- `invalid_token_contract` — proof token contract does not match server config
- `stale_payment_proof` — proof timestamp is too old or too far outside allowed skew
- `missing_nonce` — nonce is required but missing
- `invalid_wallet_signature` — wallet signature does not recover to the payer wallet
- `replayed_tx_hash` — transaction hash was already used
- `replayed_nonce` — nonce was already used
- `replayed_quote_id` — quote ID was already used
- `rpc_unavailable` — Base RPC could not be reached
- `rpc_wrong_chain` — RPC returned the wrong chain
- `tx_receipt_missing` — transaction receipt could not be found
- `tx_failed` — transaction failed onchain
- `insufficient_confirmations` — transaction does not yet have enough confirmations
- `insufficient_or_invalid_transfer` — receipt did not contain the expected transfer

## 10. Minimal curl examples

### Free search endpoint

```bash
curl "https://YOUR_API_BASE_URL/api/v1/search?q=agent%20infrastructure&source=mock"
```

### Free structured HTML extraction

```bash
curl -X POST "https://YOUR_API_BASE_URL/api/v1/structured-web/extract-html" \
  -H "Content-Type: application/json" \
  -d '{"html":"<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>","source_url":"https://acme.com"}'
```

### Pricing discovery

```bash
curl "https://YOUR_API_BASE_URL/pricing"
```

### Payment schema discovery

```bash
curl "https://YOUR_API_BASE_URL/payment/schema"
```

### Paid lead extraction

```bash
curl -X POST "https://YOUR_API_BASE_URL/api/v1/lead-extract" \
  -H "Content-Type: application/json" \
  -H "X-Payment-Format: base-usdc-onchain-v1" \
  -H "X-Payment-Proof: <base64url-encoded-json>" \
  -d '{"html":"<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>","source_url":"https://acme.com"}'
```

## 11. Minimal PowerShell examples

### Free search endpoint

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "https://YOUR_API_BASE_URL/api/v1/search?q=agent%20infrastructure&source=mock"
```

### Free structured HTML extraction

```powershell
$body = @{
  html = "<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>"
  source_url = "https://acme.com"
} | ConvertTo-Json -Compress

Invoke-RestMethod `
  -Method Post `
  -Uri "https://YOUR_API_BASE_URL/api/v1/structured-web/extract-html" `
  -ContentType "application/json" `
  -Body $body
```

### Pricing discovery

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "https://YOUR_API_BASE_URL/pricing"
```

### Payment schema discovery

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "https://YOUR_API_BASE_URL/payment/schema"
```

### Paid lead extraction

```powershell
$proof = "<base64url-encoded-json>"
$body = @{
  html = "<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>"
  source_url = "https://acme.com"
} | ConvertTo-Json -Compress

Invoke-RestMethod `
  -Method Post `
  -Uri "https://YOUR_API_BASE_URL/api/v1/lead-extract" `
  -Headers @{
    "X-Payment-Format" = "base-usdc-onchain-v1"
    "X-Payment-Proof"  = $proof
  } `
  -ContentType "application/json" `
  -Body $body
```

## 12. Example 402 response

```json
{
  "ok": false,
  "error": {
    "code": "PAYMENT_REQUIRED",
    "message": "Payment is required before this request can be processed.",
    "details": {
      "reason": "malformed_payment_proof"
    }
  },
  "meta": {
    "request_id": "req_123abc",
    "pricing_id": "lead_extract.html",
    "payment_mode": "per_request"
  },
  "payment": {
    "chain": "base",
    "token": "USDC",
    "receiver_wallet": "0xa850773dDdAc7051c9434E3b1e804531C12d265c",
    "payment_mode": "per_request",
    "payment_format": "base-usdc-onchain-v1"
  }
}
```

## 13. Implementation notes for agents

Recommended client flow:
1. call `/pricing`
2. call `/payment/schema`
3. build the exact request body
4. compute the body hash
5. submit payment on Base
6. sign the canonical message
7. attach canonical headers
8. send the paid request

Important:
- bind proof to the exact method, path, and body
- treat `402` as a machine-readable payment validation response
- inspect `error.details.reason` for the specific failure mode
