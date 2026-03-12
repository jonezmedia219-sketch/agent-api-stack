import logging

from app.billing.payment_models import PaymentContext, PaymentDecision, PaymentRequirement
from app.billing.payment_policy import get_payment_policy
from app.billing.verifiers.base_usdc_onchain import BaseUSDCOnchainVerifier
from app.billing.verifiers.stub import StubPaymentVerifier
from app.billing.verifiers.x402 import X402PaymentVerifier
from app.config import get_settings

logger = logging.getLogger("app.payment")


_VERIFIERS = {
    "stub": StubPaymentVerifier,
    "x402": X402PaymentVerifier,
    "base_usdc_onchain": BaseUSDCOnchainVerifier,
}


def resolve_requirement(endpoint: str, verifier_override: str | None = None) -> PaymentRequirement:
    policy = get_payment_policy(endpoint)
    settings = get_settings()
    selected_verifier = verifier_override or settings.payment_verifier
    if policy.get("payment_required") and selected_verifier:
        policy = {**policy, "verifier": selected_verifier}
    return PaymentRequirement(**policy)


def build_payment_context(
    *,
    endpoint: str,
    request_id: str,
    path: str,
    method: str,
    headers: dict[str, str],
    usage_context: dict[str, str | int | float | bool | None] | None = None,
    verifier_override: str | None = None,
) -> PaymentContext:
    requirement = resolve_requirement(endpoint, verifier_override=verifier_override)
    return PaymentContext(
        endpoint=endpoint,
        pricing_id=requirement.pricing_id,
        request_id=request_id,
        path=path,
        method=method,
        headers=headers,
        usage_context=usage_context or {},
        requirement=requirement,
    )


async def verify_payment(context: PaymentContext, hard_enforcement: bool = False, shadow_mode: bool = True) -> PaymentDecision:
    verifier_cls = _VERIFIERS[context.requirement.verifier]
    verifier = verifier_cls()
    decision = await verifier.verify(context, hard_enforcement=hard_enforcement, shadow_mode=shadow_mode)
    logger.info(
        "payment_decision endpoint=%s pricing_id=%s allowed=%s payment_required=%s reason=%s shadow_mode=%s verifier=%s",
        context.endpoint,
        context.pricing_id,
        decision.allowed,
        decision.payment_required,
        decision.reason,
        decision.shadow_mode,
        decision.verifier,
    )
    return decision
