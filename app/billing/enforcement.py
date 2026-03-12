import hashlib
import json

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

    enriched_usage_context = dict(usage_context or {})
    if request.method.upper() in {"POST", "PUT", "PATCH"}:
        try:
            body = await request.body()
            enriched_usage_context["body_sha256"] = hashlib.sha256(body).hexdigest()
        except Exception:
            enriched_usage_context["body_sha256"] = ""
    else:
        enriched_usage_context["body_sha256"] = ""

    context = build_payment_context(
        endpoint=endpoint,
        request_id=getattr(request.state, "request_id", "unknown"),
        path=request.url.path,
        method=request.method,
        headers={key.lower(): value for key, value in request.headers.items()},
        usage_context=enriched_usage_context,
        verifier_override=getattr(request.app.state, "payment_verifier", None),
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
            payment_format=decision.proof_format or "base-usdc-onchain-v1",
            reason=decision.reason or "payment_required",
        )
