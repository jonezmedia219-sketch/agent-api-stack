from time import perf_counter

from fastapi import APIRouter, Request

from app.billing.enforcement import enforce_payment
from app.billing.helpers import build_usage_context
from app.billing.usage import record_usage
from app.core.response_builders import build_success
from app.models.structured_web import StructuredWebData, StructuredWebExtractHTMLRequest, StructuredWebExtractRequest
from app.services.structured_web.service import extract_from_html, extract_from_url

router = APIRouter(prefix="/api/v1/structured-web", tags=["structured-web"])


@router.post("/extract")
async def extract_url(payload: StructuredWebExtractRequest, request: Request) -> dict:
    started = perf_counter()
    await enforce_payment(request, endpoint="structured_web.extract", usage_context={"mode": "url"})
    data: StructuredWebData = await extract_from_url(str(payload.url))
    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(
        request,
        api="structured_web",
        duration_ms=duration_ms,
        usage_context={"mode": "url"},
    )
    record_usage("structured_web.extract", usage_context)
    request_id = request.state.request_id
    return build_success(data=data.model_dump(), request_id=request_id, api="structured_web", started_at=started)


@router.post("/extract-html")
async def extract_html(payload: StructuredWebExtractHTMLRequest, request: Request) -> dict:
    started = perf_counter()
    await enforce_payment(request, endpoint="structured_web.extract_html", usage_context={"mode": "html"})
    data: StructuredWebData = extract_from_html(payload.html, str(payload.source_url) if payload.source_url else None)
    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(
        request,
        api="structured_web",
        duration_ms=duration_ms,
        usage_context={"mode": "html"},
    )
    record_usage("structured_web.extract_html", usage_context)
    request_id = request.state.request_id
    return build_success(data=data.model_dump(), request_id=request_id, api="structured_web", started_at=started)
