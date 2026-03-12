import base64
import hashlib
import json
import time
from unittest.mock import patch

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

from app.billing.verifiers.base_usdc_onchain import BaseUSDCOnchainVerifier

PRIVATE_KEY = "0x59c6995e998f97a5a0044966f094538b2925f5b4b8d7a7c4f8f8f8f8f8f8f8f8"
ACCOUNT = Account.from_key(PRIVATE_KEY)
RECEIVER = "0xa850773dDdAc7051c9434E3b1e804531C12d265c"
TOKEN_CONTRACT = "0x833589fCD6EDB6E08f4c7C32D4f71b54bdA02913"
TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()


def canonical_body_bytes(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def make_proof(*, pricing_id="lead_extract.html", chain_id=8453, receiver_wallet=RECEIVER, token_contract=TOKEN_CONTRACT, method="POST", path="/api/v1/lead-extract", body_sha256=None, amount="0.01", timestamp=None, nonce="nonce-1", quote_id="quote-1", tx_hash="0xabc"):
    timestamp = int(time.time()) if timestamp is None else timestamp
    body_sha256 = body_sha256 or hashlib.sha256(canonical_body_bytes(valid_payload_json())).hexdigest()
    payload = {
        "version": "base-usdc-onchain-v1",
        "chain_id": chain_id,
        "pricing_id": pricing_id,
        "payment_mode": "per_request",
        "receiver_wallet": receiver_wallet,
        "token_contract": token_contract,
        "amount": amount,
        "currency_decimals": 6,
        "request_binding": {
            "method": method,
            "path": path,
            "body_sha256": body_sha256,
        },
        "quote_id": quote_id,
        "nonce": nonce,
        "timestamp": timestamp,
        "payer_wallet": ACCOUNT.address,
        "tx_hash": tx_hash,
    }
    message = "|".join([
        payload["version"],
        str(payload["chain_id"]),
        payload["pricing_id"],
        payload["payment_mode"],
        payload["receiver_wallet"],
        payload["token_contract"],
        payload["request_binding"]["method"],
        payload["request_binding"]["path"],
        payload["request_binding"]["body_sha256"],
        payload["quote_id"],
        payload["nonce"],
        str(payload["timestamp"]),
        payload["amount"],
        payload["tx_hash"],
    ])
    signed = Account.sign_message(encode_defunct(text=message), PRIVATE_KEY)
    payload["wallet_signature"] = signed.signature.hex()
    return base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")


class FakeReceipt:
    def __init__(self, status=1, block_number=100, amount_units=10000, token_contract=TOKEN_CONTRACT, payer=ACCOUNT.address, receiver=RECEIVER):
        self.status = status
        self.blockNumber = block_number
        self.logs = [
            {
                "address": token_contract,
                "topics": [
                    Web3.to_bytes(hexstr=TRANSFER_TOPIC),
                    Web3.to_bytes(hexstr="0x" + payer.lower().replace("0x", "").rjust(64, "0")),
                    Web3.to_bytes(hexstr="0x" + receiver.lower().replace("0x", "").rjust(64, "0")),
                ],
                "data": hex(amount_units),
            }
        ]

    def __getitem__(self, item):
        return getattr(self, item)


class FakeEth:
    def __init__(self, receipt=None, block_number=101, chain_id=8453):
        self._receipt = receipt
        self.block_number = block_number
        self.chain_id = chain_id

    def get_transaction_receipt(self, _tx_hash):
        if self._receipt is None:
            raise Exception("missing")
        return self._receipt


class FakeWeb3:
    def __init__(self, receipt=None, block_number=101, connected=True, chain_id=8453):
        self.eth = FakeEth(receipt=receipt, block_number=block_number, chain_id=chain_id)
        self._connected = connected

    def is_connected(self):
        return self._connected


def valid_payload_json():
    return {"html": "<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>", "source_url": "https://acme.com"}


def test_missing_proof_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    response = client.post("/api/v1/lead-extract", json=valid_payload_json())
    assert response.status_code == 402


def test_malformed_proof_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": "bad"}, json=valid_payload_json())
    assert response.status_code == 402


def test_wrong_chain_id_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    proof = make_proof(chain_id=1)
    response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert response.status_code == 402


def test_wrong_token_contract_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    proof = make_proof(token_contract="0x1111111111111111111111111111111111111111")
    response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert response.status_code == 402


def test_wrong_receiver_wallet_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    proof = make_proof(receiver_wallet="0x1111111111111111111111111111111111111111")
    response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert response.status_code == 402


def test_wrong_pricing_id_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    proof = make_proof(pricing_id="lead_extract.url")
    response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert response.status_code == 402


def test_wrong_method_path_body_binding_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    proof = make_proof(method="GET")
    response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert response.status_code == 402


def test_invalid_wallet_signature_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    proof_payload = json.loads(base64.urlsafe_b64decode((make_proof() + "==").encode()).decode())
    proof_payload["wallet_signature"] = "0xdeadbeef"
    proof = base64.urlsafe_b64encode(json.dumps(proof_payload).encode()).decode().rstrip("=")
    response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert response.status_code == 402


def test_tx_receipt_missing_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    proof = make_proof(tx_hash="0xmissing")
    with patch("app.billing.verifiers.base_usdc_onchain.BaseUSDCOnchainVerifier._get_web3", return_value=FakeWeb3(receipt=None)):
        response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert response.status_code == 402


def test_tx_failed_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    proof = make_proof(tx_hash="0xfailed")
    with patch("app.billing.verifiers.base_usdc_onchain.BaseUSDCOnchainVerifier._get_web3", return_value=FakeWeb3(receipt=FakeReceipt(status=0))):
        response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert response.status_code == 402


def test_insufficient_amount_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    proof = make_proof(amount="0.01", tx_hash="0xlow")
    with patch("app.billing.verifiers.base_usdc_onchain.BaseUSDCOnchainVerifier._get_web3", return_value=FakeWeb3(receipt=FakeReceipt(amount_units=1))):
        response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert response.status_code == 402


def test_replayed_tx_hash_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    BaseUSDCOnchainVerifier._used_tx_hashes.clear()
    BaseUSDCOnchainVerifier._used_nonces.clear()
    BaseUSDCOnchainVerifier._used_quote_ids.clear()
    BaseUSDCOnchainVerifier._order.clear()
    proof = make_proof(tx_hash="0xreplaytx", nonce="nonce-tx", quote_id="quote-tx")
    fake_web3 = FakeWeb3(receipt=FakeReceipt())
    with patch("app.billing.verifiers.base_usdc_onchain.BaseUSDCOnchainVerifier._get_web3", return_value=fake_web3):
        first = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
        second = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert first.status_code == 200
    assert second.status_code == 402


def test_replayed_nonce_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    BaseUSDCOnchainVerifier._used_tx_hashes.clear()
    BaseUSDCOnchainVerifier._used_nonces.clear()
    BaseUSDCOnchainVerifier._used_quote_ids.clear()
    BaseUSDCOnchainVerifier._order.clear()
    fake_web3 = FakeWeb3(receipt=FakeReceipt())
    proof1 = make_proof(tx_hash="0xnonce1", nonce="dup-nonce", quote_id="quote-a")
    proof2 = make_proof(tx_hash="0xnonce2", nonce="dup-nonce", quote_id="quote-b")
    with patch("app.billing.verifiers.base_usdc_onchain.BaseUSDCOnchainVerifier._get_web3", return_value=fake_web3):
        first = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof1}, json=valid_payload_json())
        second = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof2}, json=valid_payload_json())
    assert first.status_code == 200
    assert second.status_code == 402


def test_replayed_quote_id_returns_402(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    BaseUSDCOnchainVerifier._used_tx_hashes.clear()
    BaseUSDCOnchainVerifier._used_nonces.clear()
    BaseUSDCOnchainVerifier._used_quote_ids.clear()
    BaseUSDCOnchainVerifier._order.clear()
    fake_web3 = FakeWeb3(receipt=FakeReceipt())
    proof1 = make_proof(tx_hash="0xquote1", nonce="nonce-q1", quote_id="dup-quote")
    proof2 = make_proof(tx_hash="0xquote2", nonce="nonce-q2", quote_id="dup-quote")
    with patch("app.billing.verifiers.base_usdc_onchain.BaseUSDCOnchainVerifier._get_web3", return_value=fake_web3):
        first = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof1}, json=valid_payload_json())
        second = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof2}, json=valid_payload_json())
    assert first.status_code == 200
    assert second.status_code == 402


def test_valid_proof_succeeds(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    BaseUSDCOnchainVerifier._used_tx_hashes.clear()
    BaseUSDCOnchainVerifier._used_nonces.clear()
    BaseUSDCOnchainVerifier._used_quote_ids.clear()
    BaseUSDCOnchainVerifier._order.clear()
    proof = make_proof(tx_hash="0xvalid", nonce="nonce-valid", quote_id="quote-valid")
    with patch("app.billing.verifiers.base_usdc_onchain.BaseUSDCOnchainVerifier._get_web3", return_value=FakeWeb3(receipt=FakeReceipt())):
        response = client.post("/api/v1/lead-extract", headers={"X-Payment-Format": "base-usdc-onchain-v1", "X-Payment-Proof": proof}, json=valid_payload_json())
    assert response.status_code == 200


def test_free_endpoint_still_works_without_payment(client):
    client.app.state.payment_shadow_mode = False
    client.app.state.payment_hard_enforcement = True
    client.app.state.payment_verifier = "base_usdc_onchain"
    response = client.get("/api/v1/search", params={"q": "agent infrastructure", "source": "mock"})
    assert response.status_code == 200
