from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["agent-discovery"])

SKILL_MD = """# agent-api-stack

Agent-ready API stack for search, structured web extraction, and paid lead/contact extraction.

## Summary

This service exposes:
- free endpoints for search and structured web extraction
- a paid endpoint for lead/contact extraction
- machine-readable pricing discovery
- machine-readable payment schema discovery
- onchain Base USDC payment verification with replay protection

## Discovery

Start here:
- Service root: https://agent-api-stack.onrender.com/
- OpenAPI docs: https://agent-api-stack.onrender.com/docs
- Pricing discovery: https://agent-api-stack.onrender.com/pricing
- Payment schema discovery: https://agent-api-stack.onrender.com/payment/schema

## Recommended workflow

1. Fetch https://agent-api-stack.onrender.com/
2. Read https://agent-api-stack.onrender.com/pricing
3. Read https://agent-api-stack.onrender.com/payment/schema
4. Use a free endpoint first if possible
5. For paid lead extraction:
   - construct the exact request body
   - hash the exact body
   - submit Base USDC payment
   - obtain the tx hash
   - sign the canonical message
   - assemble the proof
   - send the request with canonical payment headers
6. Never replay a used proof

## Free endpoints

- GET https://agent-api-stack.onrender.com/api/v1/search
- POST https://agent-api-stack.onrender.com/api/v1/structured-web/extract
- POST https://agent-api-stack.onrender.com/api/v1/structured-web/extract-html

These endpoints do not require payment.

## Paid endpoint

- POST https://agent-api-stack.onrender.com/api/v1/lead-extract

Pricing ID depends on mode:
- HTML mode: lead_extract.html
- URL mode: lead_extract.url

## Discovery endpoints

- GET https://agent-api-stack.onrender.com/
- GET https://agent-api-stack.onrender.com/docs
- GET https://agent-api-stack.onrender.com/pricing
- GET https://agent-api-stack.onrender.com/payment/schema

## Canonical payment headers

- X-Payment-Format: base-usdc-onchain-v1
- X-Payment-Proof: <base64url-encoded-json>

## Replay warning

Do not reuse the same payment proof.
Do not reuse the same:
- tx_hash
- nonce
- quote_id

Replayed proofs should be rejected.
"""

LLMS_TXT = """# agent-api-stack

agent-api-stack is an agent-ready API service for:
- search
- structured web extraction
- paid lead/contact extraction

It is designed to be easy for both humans and software agents to discover and use.

## Key URLs

- Service root: https://agent-api-stack.onrender.com/
- OpenAPI docs: https://agent-api-stack.onrender.com/docs
- Pricing discovery: https://agent-api-stack.onrender.com/pricing
- Payment schema discovery: https://agent-api-stack.onrender.com/payment/schema
- Integration guide: https://github.com/jonezmedia219-sketch/agent-api-stack/blob/main/docs/integration-payments.md

## Endpoint categories

Free endpoints:
- GET https://agent-api-stack.onrender.com/api/v1/search
- POST https://agent-api-stack.onrender.com/api/v1/structured-web/extract
- POST https://agent-api-stack.onrender.com/api/v1/structured-web/extract-html

Paid endpoint:
- POST https://agent-api-stack.onrender.com/api/v1/lead-extract

## Payment model

The paid endpoint uses:
- Base USDC onchain payment verification
- machine-readable pricing discovery
- machine-readable payment schema discovery
- replay protection

Canonical payment headers:
- X-Payment-Format
- X-Payment-Proof

Canonical payment format:
- base-usdc-onchain-v1

## Recommended agent flow

1. Read https://agent-api-stack.onrender.com/
2. Read https://agent-api-stack.onrender.com/pricing
3. Read https://agent-api-stack.onrender.com/payment/schema
4. Use a free endpoint when appropriate
5. For paid lead extraction, bind payment proof to the exact request body, method, and path
6. Do not replay proofs
"""


@router.get("/.well-known/skills/default/skill.md", response_class=PlainTextResponse)
async def skill_md() -> str:
    return SKILL_MD


@router.get("/llms.txt", response_class=PlainTextResponse)
async def llms_txt() -> str:
    return LLMS_TXT
