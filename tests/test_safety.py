def test_request_size_limit(client):
    oversized = "x" * 1_100_000
    response = client.post(
        "/api/v1/lead-extract",
        headers={"content-length": str(len(oversized))},
        json={"html": oversized},
    )
    assert response.status_code == 413
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "REQUEST_TOO_LARGE"


def test_cors_not_enabled_by_default(client):
    response = client.options("/api/v1/search")
    assert "access-control-allow-origin" not in response.headers
