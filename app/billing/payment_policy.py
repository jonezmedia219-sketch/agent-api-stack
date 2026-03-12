PAYMENT_POLICIES = {
    "search.query": {
        "pricing_id": "search.query",
        "payment_required": False,
        "payment_mode": "free",
        "verifier": "stub",
    },
    "structured_web.extract": {
        "pricing_id": "structured_web.extract",
        "payment_required": False,
        "payment_mode": "free",
        "verifier": "stub",
    },
    "structured_web.extract_html": {
        "pricing_id": "structured_web.extract_html",
        "payment_required": False,
        "payment_mode": "free",
        "verifier": "stub",
    },
    "lead_extract.url": {
        "pricing_id": "lead_extract.url",
        "payment_required": True,
        "payment_mode": "per_request",
        "verifier": "base_usdc_onchain",
        "chain": "base",
        "token": "USDC",
        "receiver_wallet": "0xa850773dDdAc7051c9434E3b1e804531C12d265c",
        "amount": "0.01",
    },
    "lead_extract.html": {
        "pricing_id": "lead_extract.html",
        "payment_required": True,
        "payment_mode": "per_request",
        "verifier": "base_usdc_onchain",
        "chain": "base",
        "token": "USDC",
        "receiver_wallet": "0xa850773dDdAc7051c9434E3b1e804531C12d265c",
        "amount": "0.01",
    },
}


def get_payment_policy(endpoint: str) -> dict:
    policy = PAYMENT_POLICIES.get(endpoint)
    if not policy:
        raise KeyError(f"No payment policy found for endpoint: {endpoint}")
    return policy
