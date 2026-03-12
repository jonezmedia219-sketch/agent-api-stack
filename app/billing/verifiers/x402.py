import base64
import hashlib
import hmac
import json
import time
from collections import deque

from app.billing.payment_models import PaymentContext, PaymentDecision, X402PaymentProof
from app.billing.verifiers.base import PaymentVerifier
from app.config import get_settings


class X402PaymentVerifier(PaymentVerifier):
    name = "x402"
    _used_proofs: dict[str, float] = {}
    _used_order: deque[tuple[str, float]] = deque()

    def _cleanup(self, now: float, max_skew_seconds: int) -> None:
        cutoff = now - max_skew_seconds
        while self._used_order and self._used_order[0][1] < cutoff:
            digest, _timestamp = self._used_order.popleft()
            self._used_proofs.pop(digest, None)

    def _decode_proof(self, encoded: str) -> dict:
        padded = encoded + "=" * (-len(encoded) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))

    def _signature_payload(self, proof: X402PaymentProof) -> str:
        return "|".join(
            [
                proof.version,
                proof.chain,
                proof.token,
                proof.pricing_id,
                proof.payment_mode,
                proof.receiver_wallet,
                proof.request_binding.method,
                proof.request_binding.path,
                str(proof.timestamp),
                proof.nonce,
                proof.amount,
            ]
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
        if not encoded_proof or proof_format != "x402-base-usdc-v1":
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
            proof = X402PaymentProof(**raw)
        except Exception:
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

        if proof.version != "x402-base-usdc-v1":
            reason = "invalid_payment_version"
        elif proof.chain != settings.payment_chain:
            reason = "invalid_chain"
        elif proof.token != settings.payment_token:
            reason = "invalid_token"
        elif proof.receiver_wallet.lower() != settings.payment_receiver_wallet.lower():
            reason = "invalid_receiver_wallet"
        elif proof.pricing_id != context.pricing_id:
            reason = "invalid_pricing_id"
        elif proof.request_binding.method.upper() != context.method.upper() or proof.request_binding.path != context.path:
            reason = "invalid_request_binding"
        elif settings.payment_require_nonce and not proof.nonce:
            reason = "missing_nonce"
        elif abs(int(time.time()) - proof.timestamp) > settings.payment_max_skew_seconds:
            reason = "stale_payment_proof"
        elif float(proof.amount) < float(context.requirement.amount):
            reason = "insufficient_payment_amount"
        else:
            expected_signature = hmac.new(
                settings.payment_shared_secret.encode("utf-8"),
                self._signature_payload(proof).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected_signature, proof.signature):
                reason = "invalid_signature"
            else:
                digest_source = f"{proof.nonce}:{proof.signature}:{proof.timestamp}"
                proof_digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()
                now = time.time()
                self._cleanup(now, settings.payment_max_skew_seconds)
                if proof_digest in self._used_proofs:
                    reason = "replayed_payment_proof"
                else:
                    self._used_proofs[proof_digest] = now
                    self._used_order.append((proof_digest, now))
                    return PaymentDecision(
                        allowed=True,
                        shadow_mode=shadow_mode,
                        payment_required=True,
                        reason="x402_payment_verified",
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
