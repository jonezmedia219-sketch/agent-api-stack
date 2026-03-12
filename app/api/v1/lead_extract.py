from time import perf_counter

from fastapi import APIRouter, Request

from app.billing.enforcement import enforce_payment
from app.billing.helpers import build_usage_context
from app.billing.usage import record_usage
from app.core.response_builders import build_success
from app.models.lead_extract import LeadExtractRequest
from app.services.lead_extract.service import extract_leads_from_html, extract_leads_from_url

router = APIRouter(tags=["lead-extract"])


@router.post("/api/v1/lead-extract")
async def lead_extract(payload: LeadExtractRequest, request: Request) -> dict:
    started = perf_counter()
    if payload.url:
        endpoint = "lead_extract.url"
        mode = "url"
        await enforce_payment(request, endpoint=endpoint, usage_context={"mode": mode})
        data = await extract_leads_from_url(str(payload.url))
    else:
        endpoint = "lead_extract.html"
        mode = "html"
        await enforce_payment(request, endpoint=endpoint, usage_context={"mode": mode})
        data = extract_leads_from_html(payload.html or "", str(payload.source_url) if payload.source_url else None)

    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(
        request,
        api="lead_extract",
        duration_ms=duration_ms,
        usage_context={"mode": mode},
    )
    record_usage(endpoint, usage_context)
    request_id = request.state.request_id
    return build_success(data=data.model_dump(), request_id=request_id, api="lead_extract", started_at=started)
