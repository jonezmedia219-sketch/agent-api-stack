from app.billing.payment_models import PaymentContext, PaymentDecision
from app.billing.verifiers.base import PaymentVerifier


class StubPaymentVerifier(PaymentVerifier):
    name = "stub"

    async def verify(self, context: PaymentContext, hard_enforcement: bool, shadow_mode: bool) -> PaymentDecision:
        proof = context.headers.get("x-debug-payment", "")
        has_stub_payment = proof.lower() == "ok"
        requirement = context.requirement

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

        if has_stub_payment:
            return PaymentDecision(
                allowed=True,
                shadow_mode=shadow_mode,
                payment_required=True,
                reason="stub_payment_verified",
                pricing_id=requirement.pricing_id,
                payment_mode=requirement.payment_mode,
                chain=requirement.chain,
                token=requirement.token,
                receiver_wallet=requirement.receiver_wallet,
                verifier=self.name,
            )

        if shadow_mode and not hard_enforcement:
            return PaymentDecision(
                allowed=True,
                shadow_mode=True,
                payment_required=True,
                reason="payment_missing_shadow_mode",
                pricing_id=requirement.pricing_id,
                payment_mode=requirement.payment_mode,
                chain=requirement.chain,
                token=requirement.token,
                receiver_wallet=requirement.receiver_wallet,
                verifier=self.name,
            )

        return PaymentDecision(
            allowed=False,
            shadow_mode=shadow_mode,
            payment_required=True,
            reason="payment_required",
            pricing_id=requirement.pricing_id,
            payment_mode=requirement.payment_mode,
            chain=requirement.chain,
            token=requirement.token,
            receiver_wallet=requirement.receiver_wallet,
            verifier=self.name,
        )
