from time import perf_counter

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.billing.enforcement import enforce_payment
from app.billing.helpers import build_usage_context
from app.billing.usage import record_usage
from app.core.response_builders import build_success
from app.models.extract_page import ExtractPageRequest
from app.services.extract_page.service import ExtractPageError, extract_page_from_url

router = APIRouter(tags=["extract-page"])


def _error_payload(*, code: str, message: str, retryable: bool) -> dict:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
        },
    }


@router.post("/api/v1/extract/page")
async def extract_page(payload: ExtractPageRequest, request: Request):
    started = perf_counter()
    await enforce_payment(request, endpoint="extract.page", usage_context={"mode": "url"})
    try:
        data = await extract_page_from_url(payload.url)
    except ExtractPageError as exc:
        return JSONResponse(status_code=exc.status_code, content=_error_payload(code=exc.code, message=exc.message, retryable=exc.retryable))

    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(
        request,
        api="extract_page",
        duration_ms=duration_ms,
        usage_context={"mode": "url"},
    )
    record_usage("extract.page", usage_context)
    request_id = request.state.request_id
    return build_success(data=data.model_dump(), request_id=request_id, api="extract_page", started_at=started)
