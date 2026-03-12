def test_root_discovery_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "service": "agent-api-stack",
        "docs": "/docs",
        "pricing": "/pricing",
        "payment_schema": "/payment/schema",
        "integration_guide": "https://github.com/jonezmedia219-sketch/agent-api-stack/blob/main/docs/integration-payments.md",
    }
