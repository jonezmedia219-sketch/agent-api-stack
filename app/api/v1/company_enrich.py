from time import perf_counter

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.billing.enforcement import enforce_payment
from app.billing.helpers import build_usage_context
from app.billing.usage import record_usage
from app.core.response_builders import build_success
from app.models.company_enrich import CompanyEnrichBatchData, CompanyEnrichBatchItem, CompanyEnrichBatchItemError, CompanyEnrichBatchRequest, CompanyEnrichRequest
from app.services.company_enrich.service import CompanyEnrichError, enrich_company_from_domain, enrich_company_from_domain_deep

router = APIRouter(tags=["company-enrich"])


def _error_payload(*, code: str, message: str, retryable: bool) -> dict:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
        },
    }


@router.post("/api/v1/company-enrich")
async def company_enrich(payload: CompanyEnrichRequest, request: Request):
    started = perf_counter()
    await enforce_payment(request, endpoint="company.enrich", usage_context={"mode": "domain"})
    try:
        data = await enrich_company_from_domain(payload.domain)
    except CompanyEnrichError as exc:
        return JSONResponse(status_code=exc.status_code, content=_error_payload(code=exc.code, message=exc.message, retryable=exc.retryable))

    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(
        request,
        api="company_enrich",
        duration_ms=duration_ms,
        usage_context={"mode": "domain"},
    )
    record_usage("company.enrich", usage_context)
    request_id = request.state.request_id
    return build_success(data=data.model_dump(), request_id=request_id, api="company_enrich", started_at=started)


@router.post("/api/v1/company-enrich/deep")
async def company_enrich_deep(payload: CompanyEnrichRequest, request: Request):
    started = perf_counter()
    await enforce_payment(request, endpoint="company.enrich.deep", usage_context={"mode": "domain_deep"})
    try:
        data = await enrich_company_from_domain_deep(payload.domain)
    except CompanyEnrichError as exc:
        return JSONResponse(status_code=exc.status_code, content=_error_payload(code=exc.code, message=exc.message, retryable=exc.retryable))

    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(
        request,
        api="company_enrich_deep",
        duration_ms=duration_ms,
        usage_context={"mode": "domain_deep"},
    )
    record_usage("company.enrich.deep", usage_context)
    request_id = request.state.request_id
    return build_success(data=data.model_dump(), request_id=request_id, api="company_enrich_deep", started_at=started)


@router.post("/api/v1/company-enrich/batch")
async def company_enrich_batch(payload: CompanyEnrichBatchRequest, request: Request):
    started = perf_counter()
    await enforce_payment(request, endpoint="company.enrich.batch", usage_context={"mode": "domain_batch", "count": len(payload.domains)})

    results: list[CompanyEnrichBatchItem] = []
    for domain in payload.domains:
        try:
            data = await enrich_company_from_domain(domain)
            results.append(CompanyEnrichBatchItem(domain=domain, ok=True, data=data))
        except CompanyEnrichError as exc:
            results.append(
                CompanyEnrichBatchItem(
                    domain=domain,
                    ok=False,
                    error=CompanyEnrichBatchItemError(code=exc.code, message=exc.message, retryable=exc.retryable),
                )
            )

    batch_data = CompanyEnrichBatchData(
        results=results,
        count=len(results),
        success_count=sum(1 for item in results if item.ok),
        error_count=sum(1 for item in results if not item.ok),
    )

    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(
        request,
        api="company_enrich_batch",
        duration_ms=duration_ms,
        usage_context={"mode": "domain_batch", "count": len(payload.domains)},
    )
    record_usage("company.enrich.batch", usage_context)
    request_id = request.state.request_id
    return build_success(data=batch_data.model_dump(), request_id=request_id, api="company_enrich_batch", started_at=started)


@router.post("/api/v1/company-enrich/deep/batch")
async def company_enrich_deep_batch(payload: CompanyEnrichBatchRequest, request: Request):
    started = perf_counter()
    await enforce_payment(request, endpoint="company.enrich.deep.batch", usage_context={"mode": "domain_deep_batch", "count": len(payload.domains)})

    results: list[CompanyEnrichBatchItem] = []
    for domain in payload.domains:
        try:
            data = await enrich_company_from_domain_deep(domain)
            results.append(CompanyEnrichBatchItem(domain=domain, ok=True, data=data))
        except CompanyEnrichError as exc:
            results.append(
                CompanyEnrichBatchItem(
                    domain=domain,
                    ok=False,
                    error=CompanyEnrichBatchItemError(code=exc.code, message=exc.message, retryable=exc.retryable),
                )
            )

    batch_data = CompanyEnrichBatchData(
        results=results,
        count=len(results),
        success_count=sum(1 for item in results if item.ok),
        error_count=sum(1 for item in results if not item.ok),
    )

    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(
        request,
        api="company_enrich_deep_batch",
        duration_ms=duration_ms,
        usage_context={"mode": "domain_deep_batch", "count": len(payload.domains)},
    )
    record_usage("company.enrich.deep.batch", usage_context)
    request_id = request.state.request_id
    return build_success(data=batch_data.model_dump(), request_id=request_id, api="company_enrich_deep_batch", started_at=started)
