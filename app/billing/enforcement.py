from fastapi import Request

from app.billing.payment_service import build_payment_context, verify_payment
from app.exceptions import PaymentRequiredError


async def enforce_payment(
    request: Request,
    *,
    endpoint: str,
    usage_context: dict[str, str | int | float | bool | None] | None = None,
) -> None:
    hard_enforcement = bool(getattr(request.app.state, "payment_hard_enforcement", False))
    shadow_mode = bool(getattr(request.app.state, "payment_shadow_mode", True))

    context = build_payment_context(
        endpoint=endpoint,
        request_id=getattr(request.state, "request_id", "unknown"),
        path=request.url.path,
        method=request.method,
        headers={key.lower(): value for key, value in request.headers.items()},
        usage_context=usage_context,
    )
    decision = await verify_payment(context, hard_enforcement=hard_enforcement, shadow_mode=shadow_mode)
    request.state.payment_decision = decision

    if not decision.allowed:
        raise PaymentRequiredError(
            message="Payment is required before this request can be processed.",
            pricing_id=decision.pricing_id,
            payment_mode=decision.payment_mode,
            chain=decision.chain,
            token=decision.token,
            receiver_wallet=decision.receiver_wallet,
        )
