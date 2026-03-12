def test_payment_schema_endpoint_exposes_canonical_production_format(client):
    response = client.get("/payment/schema")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True

    data = body["data"]
    assert data["payment_format"] == "base-usdc-onchain-v1"
    assert data["production"] is True
    assert data["headers"] == {
        "X-Payment-Format": "base-usdc-onchain-v1",
        "X-Payment-Proof": "<base64url-encoded-json>",
    }
    assert "X-Payment-Prof" not in data["headers"]
    assert "X-Payment-Prof" not in response.text
    assert data["signed_message_format"] == "version|chain_id|pricing_id|payment_mode|receiver_wallet|token_contract|request_binding.method|request_binding.path|request_binding.body_sha256|quote_id|nonce|timestamp|amount|tx_hash"
    assert data["encoding"] == {
        "proof": "base64url-encoded-json",
        "body_hash_algorithm": "sha256",
    }
    assert data["request_binding"] == {
        "method_field": "request_binding.method",
        "path_field": "request_binding.path",
        "body_hash_field": "request_binding.body_sha256",
    }
    assert data["replay_protection"] == {
        "unique_fields": ["tx_hash", "nonce", "quote_id"],
    }

    fields = {field["name"]: field for field in data["proof_fields"]}
    assert fields["version"]["value"] == "base-usdc-onchain-v1"
    assert fields["chain_id"]["value"] == 8453
    assert fields["payment_mode"]["value"] == "per_request"
    assert fields["receiver_wallet"]["value"] == "0xa850773dDdAc7051c9434E3b1e804531C12d265c"
    assert fields["token_contract"]["value"] == "0x833589fCD6EDB6E08f4c7C32D4f71b54bdA02913"
