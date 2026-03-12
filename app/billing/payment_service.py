import logging

from app.billing.payment_models import PaymentContext, PaymentDecision, PaymentRequirement
from app.billing.payment_policy import get_payment_policy
from app.billing.verifiers.stub import StubPaymentVerifier

logger = logging.getLogger("app.payment")


_VERIFIERS = {
    "stub": StubPaymentVerifier,
}


def resolve_requirement(endpoint: str) -> PaymentRequirement:
    policy = get_payment_policy(endpoint)
    return PaymentRequirement(**policy)


def build_payment_context(
    *,
    endpoint: str,
    request_id: str,
    path: str,
    method: str,
    headers: dict[str, str],
    usage_context: dict[str, str | int | float | bool | None] | None = None,
) -> PaymentContext:
    requirement = resolve_requirement(endpoint)
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
