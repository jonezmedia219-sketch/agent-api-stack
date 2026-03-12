from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["payment"])


@router.get("/payment/schema")
async def get_payment_schema() -> dict:
    settings = get_settings()
    return {
        "ok": True,
        "data": {
            "payment_format": "base-usdc-onchain-v1",
            "production": True,
            "headers": {
                "X-Payment-Format": "base-usdc-onchain-v1",
                "X-Payment-Proof": "<base64url-encoded-json>",
            },
            "signed_message_format": "version|chain_id|pricing_id|payment_mode|receiver_wallet|token_contract|request_binding.method|request_binding.path|request_binding.body_sha256|quote_id|nonce|timestamp|amount|tx_hash",
            "encoding": {
                "proof": "base64url-encoded-json",
                "body_hash_algorithm": "sha256",
            },
            "proof_fields": [
                {"name": "version", "type": "string", "required": True, "value": "base-usdc-onchain-v1"},
                {"name": "chain_id", "type": "integer", "required": True, "value": 8453},
                {"name": "pricing_id", "type": "string", "required": True},
                {"name": "payment_mode", "type": "string", "required": True, "value": "per_request"},
                {"name": "receiver_wallet", "type": "string", "required": True, "value": settings.payment_receiver_wallet},
                {"name": "token_contract", "type": "string", "required": True, "value": settings.payment_token_contract},
                {"name": "amount", "type": "string", "required": True},
                {"name": "currency_decimals", "type": "integer", "required": True, "value": 6},
                {
                    "name": "request_binding",
                    "type": "object",
                    "required": True,
                    "fields": [
                        {"name": "method", "type": "string", "required": True},
                        {"name": "path", "type": "string", "required": True},
                        {"name": "body_sha256", "type": "string", "required": True},
                    ],
                },
                {"name": "quote_id", "type": "string", "required": True},
                {"name": "nonce", "type": "string", "required": True},
                {"name": "timestamp", "type": "integer", "required": True},
                {"name": "payer_wallet", "type": "string", "required": True},
                {"name": "tx_hash", "type": "string", "required": True},
                {"name": "wallet_signature", "type": "string", "required": True},
            ],
            "request_binding": {
                "method_field": "request_binding.method",
                "path_field": "request_binding.path",
                "body_hash_field": "request_binding.body_sha256",
            },
            "replay_protection": {
                "unique_fields": ["tx_hash", "nonce", "quote_id"],
            },
        },
    }
