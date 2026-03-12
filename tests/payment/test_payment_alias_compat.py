def test_x_payment_prof_alias_is_accepted_for_onchain_proof(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Prof": "bad"},
        json={"html": "<html><body><h1>Acme</h1></body></html>", "source_url": "https://acme.com"},
    )

    assert response.status_code == 402
    body = response.json()
    assert body["error"]["code"] == "PAYMENT_REQUIRED"
    assert body["error"]["details"]["reason"] == "malformed_payment_proof"
    assert body["payment"]["payment_format"] == "base-usdc-onchain-v1"
