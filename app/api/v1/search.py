from time import perf_counter

from fastapi import APIRouter, Query, Request

from app.billing.helpers import build_usage_context
from app.billing.usage import record_usage
from app.core.response_builders import build_success
from app.services.search.service import search

router = APIRouter(tags=["search"])


@router.get("/api/v1/search")
async def search_endpoint(
    request: Request,
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=25),
    source: str | None = Query(None),
) -> dict:
    started = perf_counter()
    data = await search(query=q, limit=limit, source=source)
    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(
        request,
        api="search",
        duration_ms=duration_ms,
        usage_context={"query": q, "limit": limit, "source": source or "all"},
    )
    record_usage("search.query", usage_context)
    request_id = request.state.request_id
    return build_success(data=data.model_dump(), request_id=request_id, api="search", started_at=started)
