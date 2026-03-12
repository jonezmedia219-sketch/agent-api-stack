from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


T = TypeVar("T")


class MetaResponse(BaseModel):
    request_id: str
    api: str
    version: str = "v1"
    duration_ms: float | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class SuccessResponse(GenericModel, Generic[T]):
    ok: bool = True
    data: T
    meta: MetaResponse


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorDetail
    meta: dict[str, str] = Field(default_factory=dict)
