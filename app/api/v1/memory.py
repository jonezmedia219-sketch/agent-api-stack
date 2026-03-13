from time import perf_counter

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.billing.enforcement import enforce_payment
from app.billing.helpers import build_usage_context
from app.billing.usage import record_usage
from app.core.response_builders import build_success
from app.models.memory import MemoryDeleteRequest, MemorySearchRequest, MemoryStoreRequest
from app.services.memory.service import MemoryError, delete_memory, search_memories, store_memory

router = APIRouter(tags=["memory"])


def _error_payload(*, code: str, message: str, retryable: bool) -> dict:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
        },
    }


@router.post("/api/v1/memory/store")
async def memory_store(payload: MemoryStoreRequest, request: Request):
    started = perf_counter()
    await enforce_payment(request, endpoint="memory.store", usage_context={"mode": "store"})
    try:
        data = store_memory(agent_id=payload.agent_id, scope=payload.scope, content=payload.content, metadata=payload.metadata)
    except MemoryError as exc:
        return JSONResponse(status_code=exc.status_code, content=_error_payload(code=exc.code, message=exc.message, retryable=exc.retryable))

    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(request, api="memory_store", duration_ms=duration_ms, usage_context={"mode": "store"})
    record_usage("memory.store", usage_context)
    return build_success(data=data.model_dump(), request_id=request.state.request_id, api="memory_store", started_at=started)


@router.post("/api/v1/memory/search")
async def memory_search(payload: MemorySearchRequest, request: Request):
    started = perf_counter()
    await enforce_payment(request, endpoint="memory.search", usage_context={"mode": "search", "limit": payload.limit})
    try:
        data = search_memories(agent_id=payload.agent_id, query=payload.query, limit=payload.limit, scope=payload.scope)
    except MemoryError as exc:
        return JSONResponse(status_code=exc.status_code, content=_error_payload(code=exc.code, message=exc.message, retryable=exc.retryable))

    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(request, api="memory_search", duration_ms=duration_ms, usage_context={"mode": "search", "limit": payload.limit})
    record_usage("memory.search", usage_context)
    return build_success(data=data.model_dump(), request_id=request.state.request_id, api="memory_search", started_at=started)


@router.post("/api/v1/memory/delete")
async def memory_delete(payload: MemoryDeleteRequest, request: Request):
    started = perf_counter()
    await enforce_payment(request, endpoint="memory.delete", usage_context={"mode": "delete"})
    try:
        data = delete_memory(memory_id=payload.memory_id)
    except MemoryError as exc:
        return JSONResponse(status_code=exc.status_code, content=_error_payload(code=exc.code, message=exc.message, retryable=exc.retryable))

    duration_ms = round((perf_counter() - started) * 1000, 2)
    usage_context = build_usage_context(request, api="memory_delete", duration_ms=duration_ms, usage_context={"mode": "delete"})
    record_usage("memory.delete", usage_context)
    return build_success(data=data.model_dump(), request_id=request.state.request_id, api="memory_delete", started_at=started)
