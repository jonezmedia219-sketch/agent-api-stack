from pydantic import BaseModel, Field


class UsageEvent(BaseModel):
    endpoint: str
    pricing_id: str
    request_id: str
    path: str
    method: str
    api: str
    status_code: int = 200
    duration_ms: float | None = None
    usage_context: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    units: int = 1
    success: bool = True
