def test_pricing_endpoint_exposes_public_machine_readable_pricing(client):
    response = client.get("/pricing")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    endpoints = body["data"]["endpoints"]

    search_entry = next(item for item in endpoints if item["pricing_id"] == "search.query")
    assert search_entry == {
        "pricing_id": "search.query",
        "method": "GET",
        "path": "/api/v1/search",
        "payment_required": False,
        "payment_mode": "free",
    }

    paid_entry = next(item for item in endpoints if item["pricing_id"] == "lead_extract.html")
    assert paid_entry == {
        "pricing_id": "lead_extract.html",
        "method": "POST",
        "path": "/api/v1/lead-extract",
        "payment_required": True,
        "payment_mode": "per_request",
        "chain": "base",
        "token": "USDC",
        "amount": "0.01",
        "receiver_wallet": "0xa850773dDdAc7051c9434E3b1e804531C12d265c",
        "payment_format": "base-usdc-onchain-v1",
    }
