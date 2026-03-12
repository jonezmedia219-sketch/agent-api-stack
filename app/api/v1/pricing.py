from fastapi import APIRouter

from app.billing.payment_policy import PAYMENT_POLICIES

router = APIRouter(tags=["pricing"])

_ENDPOINT_HTTP_MAP = {
    "search.query": {"method": "GET", "path": "/api/v1/search"},
    "structured_web.extract": {"method": "POST", "path": "/api/v1/structured-web/extract"},
    "structured_web.extract_html": {"method": "POST", "path": "/api/v1/structured-web/extract-html"},
    "lead_extract.url": {"method": "POST", "path": "/api/v1/lead-extract"},
    "lead_extract.html": {"method": "POST", "path": "/api/v1/lead-extract"},
}


@router.get("/pricing")
async def get_pricing() -> dict:
    endpoints = []
    for pricing_id, policy in PAYMENT_POLICIES.items():
        http_info = _ENDPOINT_HTTP_MAP[pricing_id]
        entry = {
            "pricing_id": pricing_id,
            "method": http_info["method"],
            "path": http_info["path"],
            "payment_required": policy["payment_required"],
            "payment_mode": policy["payment_mode"],
        }
        if policy["payment_required"]:
            entry.update(
                {
                    "chain": policy.get("chain"),
                    "token": policy.get("token"),
                    "amount": policy.get("amount"),
                    "receiver_wallet": policy.get("receiver_wallet"),
                    "payment_format": "base-usdc-onchain-v1",
                }
            )
        endpoints.append(entry)

    return {"ok": True, "data": {"endpoints": endpoints}}
