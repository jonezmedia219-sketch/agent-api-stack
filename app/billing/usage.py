from app.billing.context import RequestUsageContext
from app.billing.metering import emit_usage_event
from app.billing.models import UsageEvent
from app.billing.pricing import get_pricing_id


def record_usage(endpoint: str, context: RequestUsageContext, success: bool = True, units: int = 1) -> UsageEvent:
    pricing_id = get_pricing_id(endpoint)
    event = UsageEvent(
        endpoint=endpoint,
        pricing_id=pricing_id,
        request_id=context.request_id,
        path=context.path,
        method=context.method,
        api=context.api,
        status_code=context.status_code,
        duration_ms=context.duration_ms,
        usage_context=context.usage_context,
        units=units,
        success=success,
    )
    emit_usage_event(event)
    return event
