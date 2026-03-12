import base64
import hashlib
import json
import time
from unittest.mock import AsyncMock, patch

from eth_account import Account
from eth_account.messages import encode_defunct

TEST_ONLY_PRIVATE_KEY = Account.create("agent-api-stack-test-only-payment-enforcement").key.hex()
ACCOUNT = Account.from_key(TEST_ONLY_PRIVATE_KEY)


def canonical_body_bytes(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def valid_payload_json():
    return {"html": "<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>", "source_url": "https://acme.com"}


def make_proof(*, tx_hash="0xabc", nonce="nonce-1", quote_id="quote-1"):
    payload = valid_payload_json()
    body_sha256 = hashlib.sha256(canonical_body_bytes(payload)).hexdigest()
    proof_payload = {
        "version": "base-usdc-onchain-v1",
        "chain_id": 8453,
        "pricing_id": "lead_extract.html",
        "payment_mode": "per_request",
        "receiver_wallet": "0xa850773dDdAc7051c9434E3b1e804531C12d265c",
        "token_contract": "0x833589fCD6EDB6E08f4c7C32D4f71b54bdA02913",
        "amount": "0.01",
        "currency_decimals": 6,
        "request_binding": {
            "method": "POST",
            "path": "/api/v1/lead-extract",
            "body_sha256": body_sha256,
        },
        "quote_id": quote_id,
        "nonce": nonce,
        "timestamp": int(time.time()),
        "payer_wallet": ACCOUNT.address,
        "tx_hash": tx_hash,
    }
    message = "|".join([
        proof_payload["version"],
        str(proof_payload["chain_id"]),
        proof_payload["pricing_id"],
        proof_payload["payment_mode"],
        proof_payload["receiver_wallet"],
        proof_payload["token_contract"],
        proof_payload["request_binding"]["method"],
        proof_payload["request_binding"]["path"],
        proof_payload["request_binding"]["body_sha256"],
        proof_payload["quote_id"],
        proof_payload["nonce"],
        str(proof_payload["timestamp"]),
        proof_payload["amount"],
        proof_payload["tx_hash"],
    ])
    signed = Account.sign_message(encode_defunct(text=message), TEST_ONLY_PRIVATE_KEY)
    proof_payload["wallet_signature"] = signed.signature.hex()
    return base64.urlsafe_b64encode(json.dumps(proof_payload).encode("utf-8")).decode("utf-8").rstrip("=")


def test_free_endpoint_without_payment_still_works(client):
    response = client.get("/api/v1/search", params={"q": "agent infrastructure", "source": "mock"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True


def test_paid_endpoint_shadow_mode_does_not_block(client, company_contact_html):
    client.app.state.payment_shadow_mode = True
    client.app.state.payment_hard_enforcement = False

    with patch("app.services.lead_extract.service.fetch_html", new=AsyncMock(return_value=(company_contact_html, "text/html"))):
        response = client.post(
            "/api/v1/lead-extract",
            json={"url": "https://acmegrowth.com/contact"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True


def test_paid_endpoint_hard_enforcement_returns_402_without_payment(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"

    response = client.post(
        "/api/v1/lead-extract",
        json={"html": "<html><body><h1>Acme</h1></body></html>", "source_url": "https://acme.com"},
    )

    assert response.status_code == 402
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "PAYMENT_REQUIRED"
    assert body["error"]["details"]["reason"] == "missing_or_invalid_payment_headers"
    assert body["meta"]["pricing_id"] == "lead_extract.html"
    assert body["payment"]["chain"] == "base"
    assert body["payment"]["token"] == "USDC"
    assert body["payment"]["receiver_wallet"] == "0xa850773dDdAc7051c9434E3b1e804531C12d265c"
    assert body["payment"]["payment_mode"] == "per_request"
    assert body["payment"]["payment_format"] == "base-usdc-onchain-v1"


def test_paid_endpoint_succeeds_with_stub_payment_proof(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Debug-Payment": "ok"},
        json={"html": "<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>", "source_url": "https://acme.com"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "hello@acme.com" in body["data"]["emails"]


def test_paid_endpoint_returns_reason_for_malformed_proof(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"

    response = client.post(
        "/api/v1/lead-extract",
        headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": "bad"},
        json=valid_payload_json(),
    )

    assert response.status_code == 402
    body = response.json()
    assert body["error"]["code"] == "PAYMENT_REQUIRED"
    assert body["error"]["details"]["reason"] == "malformed_payment_proof"
    assert body["payment"]["payment_format"] == "base-usdc-onchain-v1"


def test_paid_endpoint_returns_reason_for_replayed_tx_hash(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"

    from app.billing.verifiers.base_usdc_onchain import BaseUSDCOnchainVerifier

    BaseUSDCOnchainVerifier._used_tx_hashes.clear()
    BaseUSDCOnchainVerifier._used_nonces.clear()
    BaseUSDCOnchainVerifier._used_quote_ids.clear()
    BaseUSDCOnchainVerifier._order.clear()

    proof = make_proof(tx_hash="0xreplaypayload", nonce="nonce-replay-payload", quote_id="quote-replay-payload")

    class FakeReceipt:
        def __init__(self):
            self.status = 1
            self.blockNumber = 100
            self.logs = [{
                "address": "0x833589fCD6EDB6E08f4c7C32D4f71b54bdA02913",
                "topics": [],
                "data": "0x0",
            }]

        def __getitem__(self, item):
            return getattr(self, item)

    class FakeEth:
        chain_id = 8453
        block_number = 101

        def get_transaction_receipt(self, _tx_hash):
            return FakeReceipt()

    class FakeWeb3:
        eth = FakeEth()

        def is_connected(self):
            return True

    with patch("app.billing.verifiers.base_usdc_onchain.BaseUSDCOnchainVerifier._verify_transfer_log", return_value=True):
        with patch("app.billing.verifiers.base_usdc_onchain.BaseUSDCOnchainVerifier._get_web3", return_value=FakeWeb3()):
            first = client.post(
                "/api/v1/lead-extract",
                headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof},
                json=valid_payload_json(),
            )
            second = client.post(
                "/api/v1/lead-extract",
                headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof},
                json=valid_payload_json(),
            )

    assert first.status_code == 200
    assert second.status_code == 402
    body = second.json()
    assert body["error"]["code"] == "PAYMENT_REQUIRED"
    assert body["error"]["details"]["reason"] == "replayed_tx_hash"
    assert body["payment"]["payment_format"] == "base-usdc-onchain-v1"


def test_usage_recording_only_happens_after_successful_execution(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True

    with patch("app.api.v1.lead_extract.record_usage") as record_usage_mock:
        response = client.post(
            "/api/v1/lead-extract",
            json={"html": "<html><body><h1>Blocked</h1></body></html>", "source_url": "https://blocked.com"},
        )

    assert response.status_code == 402
    record_usage_mock.assert_not_called()
