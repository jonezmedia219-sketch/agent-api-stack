from time import perf_counter
from typing import Any


def build_success(*, data: Any, request_id: str, api: str, version: str = "v1", started_at: float | None = None) -> dict:
    meta = {
        "request_id": request_id,
        "api": api,
        "version": version,
    }
    if started_at is not None:
        meta["duration_ms"] = round((perf_counter() - started_at) * 1000, 2)
    return {"ok": True, "data": data, "meta": meta}


def build_error(*, code: str, message: str, request_id: str) -> dict:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
        "meta": {
            "request_id": request_id,
        },
    }
