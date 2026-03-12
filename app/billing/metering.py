import logging

from app.billing.models import UsageEvent

logger = logging.getLogger("app.metering")


def emit_usage_event(event: UsageEvent) -> None:
    logger.info(
        "usage_event endpoint=%s pricing_id=%s request_id=%s method=%s path=%s status_code=%s duration_ms=%s units=%s success=%s usage_context=%s",
        event.endpoint,
        event.pricing_id,
        event.request_id,
        event.method,
        event.path,
        event.status_code,
        event.duration_ms,
        event.units,
        event.success,
        event.usage_context,
    )
