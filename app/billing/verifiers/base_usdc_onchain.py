import base64
import hashlib
import json
import logging
import time
from collections import deque
from decimal import Decimal, InvalidOperation

from eth_account.messages import encode_defunct
from eth_account import Account
from web3 import Web3

from app.billing.payment_models import BaseUSDCOnchainProof, PaymentContext, PaymentDecision
from app.billing.verifiers.base import PaymentVerifier
from app.config import get_settings

TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()
logger = logging.getLogger("app.payment")


class BaseUSDCOnchainVerifier(PaymentVerifier):
    name = "base_usdc_onchain"
    _used_tx_hashes: dict[str, float] = {}
    _used_nonces: dict[str, float] = {}
    _used_quote_ids: dict[str, float] = {}
    _order: deque[tuple[str, str, float]] = deque()

    def _get_web3(self, rpc_url: str):
        return Web3(Web3.HTTPProvider(rpc_url))

    def _cleanup(self, now: float, ttl_seconds: int) -> None:
        cutoff = now - ttl_seconds
        while self._order and self._order[0][2] < cutoff:
            kind, key, _timestamp = self._order.popleft()
            if kind == "tx":
                self._used_tx_hashes.pop(key, None)
            elif kind == "nonce":
                self._used_nonces.pop(key, None)
            elif kind == "quote":
                self._used_quote_ids.pop(key, None)

    def _decode_proof(self, encoded: str) -> dict:
        padded = encoded + "=" * (-len(encoded) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))

    def _message_string(self, proof: BaseUSDCOnchainProof) -> str:
        return "|".join(
            [
                proof.version,
                str(proof.chain_id),
                proof.pricing_id,
                proof.payment_mode,
                proof.receiver_wallet,
                proof.token_contract,
                proof.request_binding.method,
                proof.request_binding.path,
                proof.request_binding.body_sha256,
                proof.quote_id,
                proof.nonce,
                str(proof.timestamp),
                proof.amount,
                proof.tx_hash,
            ]
        )

    def _required_units(self, amount: str, decimals: int) -> int:
        try:
            value = Decimal(amount)
        except InvalidOperation as exc:
            raise ValueError("Invalid payment amount format.") from exc
        multiplier = Decimal(10) ** decimals
        return int(value * multiplier)

    def _verify_signature(self, proof: BaseUSDCOnchainProof) -> bool:
        try:
            message = encode_defunct(text=self._message_string(proof))
            recovered = Account.recover_message(message, signature=proof.wallet_signature)
            return recovered.lower() == proof.payer_wallet.lower()
        except Exception:
            return False

    def _verify_transfer_log(self, receipt, proof: BaseUSDCOnchainProof, required_units: int, token_contract: str, receiver_wallet: str) -> bool:
        receiver_topic = proof.receiver_wallet.lower().replace("0x", "").rjust(64, "0")
        payer_topic = proof.payer_wallet.lower().replace("0x", "").rjust(64, "0")
        transfer_topic = TRANSFER_TOPIC.lower().replace("0x", "")
        for log in receipt["logs"]:
            if log["address"].lower() != token_contract.lower():
                continue
            topics = []
            for topic in log["topics"]:
                if hasattr(topic, "hex"):
                    topics.append(topic.hex().lower().replace("0x", ""))
                else:
                    topics.append(str(topic).lower().replace("0x", ""))
            if len(topics) < 3:
                continue
            if topics[0] != transfer_topic:
                continue
            if topics[1] != payer_topic:
                continue
            if topics[2] != receiver_topic:
                continue
            data = log["data"]
            value = int(data.hex(), 16) if hasattr(data, "hex") else int(data, 16)
            if value >= required_units and proof.receiver_wallet.lower() == receiver_wallet.lower():
                return True
        return False

    def _log_payment_outcome(self, *, event: str, outcome: str, reason: str, context: PaymentContext, proof: BaseUSDCOnchainProof | None = None, payment_format: str | None = None) -> None:
        logger.info(
            "%s request_id=%s endpoint=%s pricing_id=%s verifier=%s payment_format=%s path=%s method=%s payer_wallet=%s receiver_wallet=%s tx_hash=%s nonce=%s quote_id=%s reason=%s outcome=%s",
            event,
            context.request_id,
            context.endpoint,
            context.pricing_id,
            self.name,
            payment_format or (proof.version if proof else None),
            context.path,
            context.method,
            proof.payer_wallet if proof else None,
            proof.receiver_wallet if proof else context.requirement.receiver_wallet,
            proof.tx_hash if proof else None,
            proof.nonce if proof else None,
            proof.quote_id if proof else None,
            reason,
            outcome,
        )

    async def verify(self, context: PaymentContext, hard_enforcement: bool, shadow_mode: bool) -> PaymentDecision:
        requirement = context.requirement
        settings = get_settings()

        if not requirement.payment_required:
            return PaymentDecision(
                allowed=True,
                shadow_mode=shadow_mode,
                payment_required=False,
                reason="free_endpoint",
                pricing_id=requirement.pricing_id,
                payment_mode=requirement.payment_mode,
                verifier=self.name,
            )

        proof_format = context.headers.get("x-payment-format", "")
        encoded_proof = context.headers.get("x-payment-proof", "") or context.headers.get("x-payment-prof", "")
        if not encoded_proof or proof_format != "base-usdc-onchain-v1":
            self._log_payment_outcome(
                event="payment_rejected",
                outcome="rejected",
                reason="missing_or_invalid_payment_headers",
                context=context,
                payment_format=proof_format or None,
            )
            return PaymentDecision(
                allowed=False if hard_enforcement else shadow_mode,
                shadow_mode=shadow_mode,
                payment_required=True,
                reason="missing_or_invalid_payment_headers",
                pricing_id=requirement.pricing_id,
                payment_mode=requirement.payment_mode,
                chain=requirement.chain,
                token=requirement.token,
                receiver_wallet=requirement.receiver_wallet,
                verifier=self.name,
            )

        try:
            raw = self._decode_proof(encoded_proof)
            proof = BaseUSDCOnchainProof(**raw)
        except Exception:
            self._log_payment_outcome(
                event="payment_rejected",
                outcome="rejected",
                reason="malformed_payment_proof",
                context=context,
                payment_format=proof_format or None,
            )
            return PaymentDecision(
                allowed=False if hard_enforcement else shadow_mode,
                shadow_mode=shadow_mode,
                payment_required=True,
                reason="malformed_payment_proof",
                pricing_id=requirement.pricing_id,
                payment_mode=requirement.payment_mode,
                chain=requirement.chain,
                token=requirement.token,
                receiver_wallet=requirement.receiver_wallet,
                verifier=self.name,
            )

        if proof.chain_id != 8453:
            reason = "invalid_chain_id"
        elif proof.pricing_id != context.pricing_id:
            reason = "invalid_pricing_id"
        elif proof.request_binding.method.upper() != context.method.upper() or proof.request_binding.path != context.path:
            reason = "invalid_request_binding"
        else:
            expected_body_hash = str(context.usage_context.get("body_sha256", ""))
            if proof.request_binding.body_sha256 != expected_body_hash:
                reason = "invalid_request_body_binding"
            elif proof.receiver_wallet.lower() != settings.payment_receiver_wallet.lower():
                reason = "invalid_receiver_wallet"
            elif proof.token_contract.lower() != settings.payment_token_contract.lower():
                reason = "invalid_token_contract"
            elif abs(int(time.time()) - proof.timestamp) > settings.payment_max_skew_seconds:
                reason = "stale_payment_proof"
            elif settings.payment_require_nonce and not proof.nonce:
                reason = "missing_nonce"
            elif not self._verify_signature(proof):
                reason = "invalid_wallet_signature"
            else:
                now = time.time()
                self._cleanup(now, settings.payment_max_skew_seconds + 600)
                if proof.tx_hash.lower() in self._used_tx_hashes:
                    reason = "replayed_tx_hash"
                elif proof.nonce in self._used_nonces:
                    reason = "replayed_nonce"
                elif proof.quote_id in self._used_quote_ids:
                    reason = "replayed_quote_id"
                else:
                    try:
                        web3 = self._get_web3(settings.base_rpc_url)
                        if not web3.is_connected():
                            reason = "rpc_unavailable"
                        elif web3.eth.chain_id != 8453:
                            reason = "rpc_wrong_chain"
                        else:
                            receipt = web3.eth.get_transaction_receipt(proof.tx_hash)
                            if not receipt:
                                reason = "tx_receipt_missing"
                            elif receipt.status != 1:
                                reason = "tx_failed"
                            elif (web3.eth.block_number - receipt.blockNumber + 1) < settings.payment_min_confirmations:
                                reason = "insufficient_confirmations"
                            else:
                                required_units = self._required_units(requirement.amount, proof.currency_decimals)
                                if not self._verify_transfer_log(
                                    receipt,
                                    proof,
                                    required_units,
                                    settings.payment_token_contract,
                                    settings.payment_receiver_wallet,
                                ):
                                    reason = "insufficient_or_invalid_transfer"
                                else:
                                    self._used_tx_hashes[proof.tx_hash.lower()] = now
                                    self._used_nonces[proof.nonce] = now
                                    self._used_quote_ids[proof.quote_id] = now
                                    self._order.append(("tx", proof.tx_hash.lower(), now))
                                    self._order.append(("nonce", proof.nonce, now))
                                    self._order.append(("quote", proof.quote_id, now))
                                    self._log_payment_outcome(
                                        event="payment_verified",
                                        outcome="success",
                                        reason="base_usdc_onchain_verified",
                                        context=context,
                                        proof=proof,
                                    )
                                    return PaymentDecision(
                                        allowed=True,
                                        shadow_mode=shadow_mode,
                                        payment_required=True,
                                        reason="base_usdc_onchain_verified",
                                        pricing_id=requirement.pricing_id,
                                        payment_mode=requirement.payment_mode,
                                        chain=requirement.chain,
                                        token=requirement.token,
                                        receiver_wallet=requirement.receiver_wallet,
                                        payer=proof.payer_wallet,
                                        verifier=self.name,
                                        proof_format=proof.version,
                                        amount=proof.amount,
                                        nonce=proof.nonce,
                                        timestamp=proof.timestamp,
                                        tx_hash=proof.tx_hash,
                                        quote_id=proof.quote_id,
                                    )
                    except Exception:
                        reason = "tx_receipt_missing"

        self._log_payment_outcome(
            event="payment_rejected",
            outcome="rejected",
            reason=reason,
            context=context,
            proof=locals().get("proof"),
            payment_format=proof_format or (locals().get("proof").version if locals().get("proof") else None),
        )
        return PaymentDecision(
            allowed=False if hard_enforcement else shadow_mode,
            shadow_mode=shadow_mode,
            payment_required=True,
            reason=reason,
            pricing_id=requirement.pricing_id,
            payment_mode=requirement.payment_mode,
            chain=requirement.chain,
            token=requirement.token,
            receiver_wallet=requirement.receiver_wallet,
            verifier=self.name,
        )
