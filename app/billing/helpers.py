from fastapi import Request

from app.billing.context import RequestUsageContext


def build_usage_context(
    request: Request,
    *,
    api: str,
    duration_ms: float | None = None,
    status_code: int = 200,
    usage_context: dict[str, str | int | float | bool | None] | None = None,
) -> RequestUsageContext:
    return RequestUsageContext(
        request_id=getattr(request.state, "request_id", "unknown"),
        path=request.url.path,
        method=request.method,
        api=api,
        status_code=status_code,
        duration_ms=duration_ms,
        usage_context=usage_context or {},
    )
