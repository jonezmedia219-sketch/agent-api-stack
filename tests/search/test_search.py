def test_search_success_default_source(client):
    response = client.get("/api/v1/search", params={"q": "agent infrastructure", "limit": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["query"] == "agent infrastructure"
    assert body["data"]["count"] == 2
    assert len(body["data"]["results"]) == 2
    assert body["data"]["results"][0]["source"] == "mock"
    assert body["data"]["results"][0]["rank"] == 1


def test_search_success_specific_source(client):
    response = client.get("/api/v1/search", params={"q": "lead extraction", "source": "mock"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["sources"] == ["mock"]


def test_search_validation_missing_query(client):
    response = client.get("/api/v1/search")
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "REQUEST_VALIDATION_ERROR"


def test_search_validation_invalid_source(client):
    response = client.get("/api/v1/search", params={"q": "agent tools", "source": "unknown"})
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
