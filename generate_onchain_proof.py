import argparse
import base64
import hashlib
import json
import secrets
import time

from eth_account import Account
from eth_account.messages import encode_defunct

REQUEST_BODY = '{"html":"<html><body><h1>Acme</h1><p>Email hello@acme.com</p></body></html>","source_url":"https://acme.com"}'

CHAIN_ID = 8453
PRICING_ID = "lead_extract.html"
PAYMENT_MODE = "per_request"
RECEIVER_WALLET = "0xa850773dDdAc7051c9434E3b1e804531C12d265c"
TOKEN_CONTRACT = "0x833589fCD6EDB6E08f4c7C32D4f71b54bdA02913"
AMOUNT = "0.01"
CURRENCY_DECIMALS = 6
REQUEST_METHOD = "POST"
REQUEST_PATH = "/api/v1/lead-extract"
PAYMENT_FORMAT = "base-usdc-onchain-v1"


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Base USDC onchain payment proof for one live lead_extract request."
    )
    parser.add_argument(
        "--private-key",
        required=True,
        help="Payer wallet private key",
    )
    parser.add_argument(
        "--tx-hash",
        required=True,
        help="Real Base USDC transfer tx hash",
    )
    parser.add_argument(
        "--api-url",
        required=True,
        help="Base API URL, e.g. https://your-api.onrender.com",
    )
    parser.add_argument(
        "--quote-id",
        default=None,
        help="Optional quote_id",
    )
    parser.add_argument(
        "--nonce",
        default=None,
        help="Optional nonce",
    )
    args = parser.parse_args()

    quote_id = args.quote_id or f"quote-{secrets.token_hex(8)}"
    nonce = args.nonce or f"nonce-{secrets.token_hex(8)}"
    timestamp = int(time.time())

    body_sha256 = hashlib.sha256(REQUEST_BODY.encode("utf-8")).hexdigest()

    acct = Account.from_key(args.private_key)
    payer_wallet = acct.address

    message = "|".join(
        [
            PAYMENT_FORMAT,
            str(CHAIN_ID),
            PRICING_ID,
            PAYMENT_MODE,
            RECEIVER_WALLET,
            TOKEN_CONTRACT,
            REQUEST_METHOD,
            REQUEST_PATH,
            body_sha256,
            quote_id,
            nonce,
            str(timestamp),
            AMOUNT,
            args.tx_hash,
        ]
    )

    signed = Account.sign_message(encode_defunct(text=message), args.private_key)

    proof = {
        "version": PAYMENT_FORMAT,
        "chain_id": CHAIN_ID,
        "pricing_id": PRICING_ID,
        "payment_mode": PAYMENT_MODE,
        "receiver_wallet": RECEIVER_WALLET,
        "token_contract": TOKEN_CONTRACT,
        "amount": AMOUNT,
        "currency_decimals": CURRENCY_DECIMALS,
        "request_binding": {
            "method": REQUEST_METHOD,
            "path": REQUEST_PATH,
            "body_sha256": body_sha256,
        },
        "quote_id": quote_id,
        "nonce": nonce,
        "timestamp": timestamp,
        "payer_wallet": payer_wallet,
        "tx_hash": args.tx_hash,
        "wallet_signature": signed.signature.hex(),
    }

    encoded_proof = base64url_encode(
        json.dumps(proof, separators=(",", ":")).encode("utf-8")
    )

    api_url = args.api_url.rstrip("/")
    curl_command = (
        f"curl -X POST {api_url}{REQUEST_PATH} "
        f'-H "Content-Type: application/json" '
        f'-H "X-Payment-Format: {PAYMENT_FORMAT}" '
        f'-H "X-Payment-Proof: {encoded_proof}" '
        f"-d '{REQUEST_BODY}'"
    )

    print("REQUEST_BODY:")
    print(REQUEST_BODY)
    print()
    print("BODY_SHA256:")
    print(body_sha256)
    print()
    print("PAYER_WALLET:")
    print(payer_wallet)
    print()
    print("QUOTE_ID:")
    print(quote_id)
    print()
    print("NONCE:")
    print(nonce)
    print()
    print("TIMESTAMP:")
    print(timestamp)
    print()
    print("MESSAGE_TO_SIGN:")
    print(message)
    print()
    print("WALLET_SIGNATURE:")
    print(signed.signature.hex())
    print()
    print("PROOF_JSON:")
    print(json.dumps(proof, indent=2))
    print()
    print("X-PAYMENT-PROOF:")
    print(encoded_proof)
    print()
    print("CURL:")
    print(curl_command)


if __name__ == "__main__":
    main()
