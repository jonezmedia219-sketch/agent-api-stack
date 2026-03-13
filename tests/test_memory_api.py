from pathlib import Path


def _set_memory_db(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MEMORY_DB_PATH", str(tmp_path / "memory.sqlite3"))


def test_memory_store_returns_200_and_creates_memory(client, monkeypatch, tmp_path):
    _set_memory_db(monkeypatch, tmp_path)
    response = client.post(
        "/api/v1/memory/store",
        json={
            "agent_id": "sales-bot",
            "scope": "user_preference",
            "content": "User prefers Stripe over PayPal.",
            "metadata": {"user_id": "u_123", "source": "chat"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["memory_id"].startswith("mem_")
    assert data["agent_id"] == "sales-bot"
    assert data["scope"] == "user_preference"
    assert data["content"] == "User prefers Stripe over PayPal."
    assert data["metadata"] == {"user_id": "u_123", "source": "chat"}
    assert data["created_at"]


def test_memory_search_returns_stored_memory_for_matching_query(client, monkeypatch, tmp_path):
    _set_memory_db(monkeypatch, tmp_path)
    client.post("/api/v1/memory/store", json={"agent_id": "sales-bot", "scope": "user_preference", "content": "User prefers Stripe over PayPal.", "metadata": {}})

    response = client.post("/api/v1/memory/search", json={"agent_id": "sales-bot", "query": "stripe preference", "limit": 5, "scope": "user_preference"})

    assert response.status_code == 200
    results = response.json()["data"]["results"]
    assert len(results) == 1
    assert results[0]["content"] == "User prefers Stripe over PayPal."
    assert results[0]["scope"] == "user_preference"
    assert results[0]["score"] > 0


def test_memory_search_respects_agent_id_separation(client, monkeypatch, tmp_path):
    _set_memory_db(monkeypatch, tmp_path)
    client.post("/api/v1/memory/store", json={"agent_id": "sales-bot", "scope": "prefs", "content": "Stripe is preferred.", "metadata": {}})
    client.post("/api/v1/memory/store", json={"agent_id": "support-bot", "scope": "prefs", "content": "Stripe is preferred.", "metadata": {}})

    response = client.post("/api/v1/memory/search", json={"agent_id": "support-bot", "query": "stripe", "limit": 5})

    assert response.status_code == 200
    results = response.json()["data"]["results"]
    assert len(results) == 1
    assert results[0]["metadata"] == {}


def test_memory_search_respects_optional_scope(client, monkeypatch, tmp_path):
    _set_memory_db(monkeypatch, tmp_path)
    client.post("/api/v1/memory/store", json={"agent_id": "sales-bot", "scope": "user_preference", "content": "User prefers Stripe.", "metadata": {}})
    client.post("/api/v1/memory/store", json={"agent_id": "sales-bot", "scope": "account_note", "content": "Stripe account is active.", "metadata": {}})

    response = client.post("/api/v1/memory/search", json={"agent_id": "sales-bot", "query": "stripe", "limit": 5, "scope": "user_preference"})

    assert response.status_code == 200
    results = response.json()["data"]["results"]
    assert len(results) == 1
    assert results[0]["scope"] == "user_preference"


def test_memory_delete_removes_a_memory(client, monkeypatch, tmp_path):
    _set_memory_db(monkeypatch, tmp_path)
    store = client.post("/api/v1/memory/store", json={"agent_id": "sales-bot", "scope": "prefs", "content": "Delete me", "metadata": {}})
    memory_id = store.json()["data"]["memory_id"]

    response = client.post("/api/v1/memory/delete", json={"memory_id": memory_id})
    assert response.status_code == 200
    assert response.json()["data"] == {"deleted": True, "memory_id": memory_id}

    search = client.post("/api/v1/memory/search", json={"agent_id": "sales-bot", "query": "delete", "limit": 5})
    assert search.status_code == 200
    assert search.json()["data"]["results"] == []


def test_memory_delete_unknown_memory_returns_not_found(client, monkeypatch, tmp_path):
    _set_memory_db(monkeypatch, tmp_path)
    response = client.post("/api/v1/memory/delete", json={"memory_id": "mem_missing"})

    assert response.status_code == 404
    assert response.json() == {
        "ok": False,
        "error": {
            "code": "NOT_FOUND",
            "message": "Memory not found.",
            "retryable": False,
        },
    }


def test_memory_tools_and_pricing_metadata_are_exposed(client, monkeypatch, tmp_path):
    _set_memory_db(monkeypatch, tmp_path)

    tools_response = client.get("/tools")
    assert tools_response.status_code == 200
    tools = tools_response.json()["data"]["tools"]

    store_tool = next(item for item in tools if item["pricing_id"] == "memory.store")
    search_tool = next(item for item in tools if item["pricing_id"] == "memory.search")
    delete_tool = next(item for item in tools if item["pricing_id"] == "memory.delete")

    assert store_tool["endpoint"] == "/api/v1/memory/store"
    assert store_tool["payment_required"] is False
    assert search_tool["endpoint"] == "/api/v1/memory/search"
    assert search_tool["payment_required"] is True
    assert search_tool["payment_format"] == "base-usdc-onchain-v1"
    assert delete_tool["endpoint"] == "/api/v1/memory/delete"
    assert delete_tool["payment_required"] is False

    pricing_response = client.get("/pricing")
    assert pricing_response.status_code == 200
    endpoints = pricing_response.json()["data"]["endpoints"]

    store_entry = next(item for item in endpoints if item["pricing_id"] == "memory.store")
    search_entry = next(item for item in endpoints if item["pricing_id"] == "memory.search")
    delete_entry = next(item for item in endpoints if item["pricing_id"] == "memory.delete")

    assert store_entry == {
        "pricing_id": "memory.store",
        "method": "POST",
        "path": "/api/v1/memory/store",
        "payment_required": False,
        "payment_mode": "free",
    }
    assert search_entry == {
        "pricing_id": "memory.search",
        "method": "POST",
        "path": "/api/v1/memory/search",
        "payment_required": True,
        "payment_mode": "per_request",
        "chain": "base",
        "token": "USDC",
        "amount": "0.001",
        "receiver_wallet": "0xa850773dDdAc7051c9434E3b1e804531C12d265c",
        "payment_format": "base-usdc-onchain-v1",
    }
    assert delete_entry == {
        "pricing_id": "memory.delete",
        "method": "POST",
        "path": "/api/v1/memory/delete",
        "payment_required": False,
        "payment_mode": "free",
    }
