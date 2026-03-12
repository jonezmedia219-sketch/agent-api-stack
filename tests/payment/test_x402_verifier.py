import base64
import hashlib
import hmac
import json
import time

from app.billing.verifiers.x402 import X402PaymentVerifier

RECEIVER = "0xa850773dDdAc7051c9434E3b1e804531C12d265c"
SECRET = "change-me-before-production"


def make_proof(*, pricing_id="lead_extract.html", chain="base", token="USDC", receiver_wallet=RECEIVER, amount="0.01", method="POST", path="/api/v1/lead-extract", timestamp=None, nonce="nonce-123", tx_hash="0xabc", version="x402-base-usdc-v1"):
    timestamp = int(time.time()) if timestamp is None else timestamp
    payload = {
        "version": version,
        "chain": chain,
        "token": token,
        "pricing_id": pricing_id,
        "payment_mode": "per_request",
        "receiver_wallet": receiver_wallet,
        "payer_wallet": "0xPAYER000000000000000000000000000000000001",
        "amount": amount,
        "currency_decimals": 6,
        "request_binding": {
            "method": method,
            "path": path,
        },
        "timestamp": timestamp,
        "nonce": nonce,
        "tx_hash": tx_hash,
    }
    signing_payload = "|".join([
        payload["version"],
        payload["chain"],
        payload["token"],
        payload["pricing_id"],
        payload["payment_mode"],
        payload["receiver_wallet"],
        payload["request_binding"]["method"],
        payload["request_binding"]["path"],
        str(payload["timestamp"]),
        payload["nonce"],
        payload["amount"],
    ])
    payload["signature"] = hmac.new(SECRET.encode("utf-8"), signing_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    return encoded


def test_missing_proof_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "x402"

    response = client.post(
        "/api/v1/lead-extract",
        json={"html": "<html><body><h1>Acme</h1></body></html>", "source_url": "https://acme.com"},
    )
    assert response.status_code == 402


def test_malformed_proof_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "x402"

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "x402-base-usdc-v1", "X-Payment-Proof": "not-base64"},
        json={"html": "<html><body><h1>Acme</h1></body></html>", "source_url": "https://acme.com"},
    )
    assert response.status_code == 402


def test_wrong_chain_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "x402"
    proof = make_proof(chain="ethereum", nonce="nonce-chain")

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "x402-base-usdc-v1", "X-Payment-Proof": proof},
        json={"html": "<html><body><h1>Acme</h1></body></html>", "source_url": "https://acme.com"},
    )
    assert response.status_code == 402


def test_wrong_token_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "x402"
    proof = make_proof(token="ETH", nonce="nonce-token")

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "x402-base-usdc-v1", "X-Payment-Proof": proof},
        json={"html": "<html><body><h1>Acme</h1></body></html>", "source_url": "https://acme.com"},
    )
    assert response.status_code == 402


def test_wrong_receiver_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "x402"
    proof = make_proof(receiver_wallet="0x1111111111111111111111111111111111111111", nonce="nonce-receiver")

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "x402-base-usdc-v1", "X-Payment-Proof": proof},
        json={"html": "<html><body><h1>Acme</h1></body></html>", "source_url": "https://acme.com"},
    )
    assert response.status_code == 402


def test_wrong_pricing_id_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "x402"
    proof = make_proof(pricing_id="lead_extract.url", nonce="nonce-pricing")

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "x402-base-usdc-v1", "X-Payment-Proof": proof},
        json={"html": "<html><body><h1>Acme</h1></body></html>", "source_url": "https://acme.com"},
    )
    assert response.status_code == 402


def test_stale_proof_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "x402"
    stale_time = int(time.time()) - 1000
    proof = make_proof(timestamp=stale_time, nonce="nonce-stale")

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "x402-base-usdc-v1", "X-Payment-Proof": proof},
        json={"html": "<html><body><h1>Acme</h1></body></html>", "source_url": "https://acme.com"},
    )
    assert response.status_code == 402


def test_replayed_proof_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "x402"
    X402PaymentVerifier._used_proofs.clear()
    X402PaymentVerifier._used_order.clear()
    proof = make_proof(nonce="nonce-replay")

    first = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "x402-base-usdc-v1", "X-Payment-Proof": proof},
        json={"html": "<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>", "source_url": "https://acme.com"},
    )
    second = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "x402-base-usdc-v1", "X-Payment-Proof": proof},
        json={"html": "<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>", "source_url": "https://acme.com"},
    )

    assert first.status_code == 200
    assert second.status_code == 402


def test_valid_proof_succeeds(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "x402"
    X402PaymentVerifier._used_proofs.clear()
    X402PaymentVerifier._used_order.clear()
    proof = make_proof(nonce="nonce-valid")

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "x402-base-usdc-v1", "X-Payment-Proof": proof},
        json={"html": "<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>", "source_url": "https://acme.com"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_free_endpoint_still_works_without_payment_under_x402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "x402"

    response = client.get("/api/v1/search", params={"q": "agent infrastructure", "source": "mock"})
    assert response.status_code == 200
    assert response.json()["ok"] is True
