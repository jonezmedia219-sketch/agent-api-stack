def test_tools_endpoint_lists_extract_page_and_paid_tools(client):
    response = client.get("/tools")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    tools = body["data"]["tools"]

    extract_page_tool = next(item for item in tools if item["pricing_id"] == "extract.page")
    assert extract_page_tool["name"] == "extract_page"
    assert extract_page_tool["category"] == "structured_extraction"
    assert extract_page_tool["endpoint"] == "/api/v1/extract/page"
    assert extract_page_tool["method"] == "POST"
    assert extract_page_tool["payment_required"] is False
    assert extract_page_tool["payment_format"] is None
    assert "url" in extract_page_tool["expected_inputs"]["json_body"]

    paid_tool = next(item for item in tools if item["pricing_id"] == "lead_extract.html")
    assert paid_tool["payment_required"] is True
    assert paid_tool["payment_format"] == "base-usdc-onchain-v1"


def test_pricing_endpoint_lists_extract_page_metadata(client):
    response = client.get("/pricing")

    assert response.status_code == 200
    body = response.json()
    endpoints = body["data"]["endpoints"]
    entry = next(item for item in endpoints if item["pricing_id"] == "extract.page")
    assert entry == {
        "pricing_id": "extract.page",
        "method": "POST",
        "path": "/api/v1/extract/page",
        "payment_required": False,
        "payment_mode": "free",
    }
